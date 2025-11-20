from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Optional

logger = logging.getLogger(__name__)


SectionSoftType = Literal[
    "intro_like",
    "verse_like",
    "chorus_like",
    "bridge_like",
    "outro_like",
    "other",
]


@dataclass(slots=True)
class SectionInference:
    id: str
    index: int
    start_sec: float
    end_sec: float
    duration_sec: float
    label_raw: int
    type_soft: SectionSoftType
    confidence: float
    display_name: str


def _normalize(values: Iterable[float]) -> List[float]:
    values = list(values)
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if abs(vmin - vmax) < 1e-9:
        return [0.5 for _ in values]
    return [(value - vmin) / (vmax - vmin) for value in values]


def _merge_consecutive_sections(sections: List[SectionInference]) -> List[SectionInference]:
    """
    Merge consecutive sections that have the same type_soft.
    
    For example: [Intro, Intro 2] -> [Intro]
                [Chorus 2, Chorus 3] -> [Chorus 2]
    
    Args:
        sections: List of SectionInference objects, assumed to be sorted by start_sec
    
    Returns:
        New list with consecutive same-type sections merged
    """
    if len(sections) <= 1:
        return sections
    
    merged: List[SectionInference] = []
    current_group: List[SectionInference] = [sections[0]]
    
    for section in sections[1:]:
        # If same type as current group, add to group
        if section.type_soft == current_group[0].type_soft:
            current_group.append(section)
        else:
            # Different type, merge current group and start new one
            merged.append(_merge_section_group(current_group))
            current_group = [section]
    
    # Don't forget the last group
    if current_group:
        merged.append(_merge_section_group(current_group))
    
    # Re-assign display names with correct ordinals
    counters: Dict[SectionSoftType, int] = {}
    for section in merged:
        if section.type_soft not in counters:
            counters[section.type_soft] = 0
        counters[section.type_soft] += 1
        ordinal = counters[section.type_soft]
        
        if section.type_soft == "chorus_like":
            section.display_name = f"Chorus {ordinal}"
        elif section.type_soft == "verse_like":
            section.display_name = f"Verse {ordinal}"
        elif section.type_soft == "intro_like":
            section.display_name = "Intro" if ordinal == 1 else f"Intro {ordinal}"
        elif section.type_soft == "outro_like":
            section.display_name = "Outro" if ordinal == 1 else f"Outro {ordinal}"
        elif section.type_soft == "bridge_like":
            section.display_name = "Bridge" if ordinal == 1 else f"Bridge {ordinal}"
        else:
            letter = chr(ord("A") + section.index)
            section.display_name = f"Section {letter}"
    
    return merged


def _merge_section_group(group: List[SectionInference]) -> SectionInference:
    """
    Merge a group of consecutive sections with the same type into a single section.
    
    Takes the earliest start_sec, latest end_sec, and averages confidence.
    Uses the first section's label_raw and index.
    """
    if len(group) == 1:
        return group[0]
    
    start_sec = min(s.start_sec for s in group)
    end_sec = max(s.end_sec for s in group)
    duration_sec = end_sec - start_sec
    avg_confidence = sum(s.confidence for s in group) / len(group)
    
    return SectionInference(
        id=group[0].id,  # Keep the first section's ID
        index=group[0].index,  # Keep the first section's index
        start_sec=start_sec,
        end_sec=end_sec,
        duration_sec=duration_sec,
        label_raw=group[0].label_raw,  # Keep the first section's raw label
        type_soft=group[0].type_soft,
        confidence=round(avg_confidence, 3),
        display_name=group[0].display_name,  # Will be reassigned later
    )


def _cluster_similar_labels(labels: List[int], similarity_threshold: int) -> Dict[int, int]:
    """
    Cluster labels that are within similarity_threshold distance.
    
    Returns a mapping from original label to cluster representative (lowest label in cluster).
    
    Args:
        labels: List of Audjust label values (0-1000)
        similarity_threshold: Max distance between labels to be considered similar
    
    Returns:
        Dict mapping each label to its cluster representative
    """
    unique_labels = sorted(set(labels))
    if not unique_labels:
        return {}
    
    # Group labels into clusters using a simple greedy approach
    clusters: Dict[int, int] = {}  # label -> cluster_representative
    
    for label in unique_labels:
        # Check if this label is close to any existing cluster representative
        assigned = False
        for cluster_rep in sorted(set(clusters.values())):
            if abs(label - cluster_rep) <= similarity_threshold:
                clusters[label] = cluster_rep
                assigned = True
                break
        
        # If not close to any existing cluster, create a new cluster
        if not assigned:
            clusters[label] = label
    
    return clusters


def infer_section_types(
    audjust_sections: List[dict],
    energy_per_section: List[float],
    vocals_per_section: Optional[List[float]] = None,
) -> List[SectionInference]:
    """
    Infer soft section types (intro/verse/chorus/bridge/outro/other) from:
      - Audjust structure segments: [{'startMs', 'endMs', 'label'}, ...]
      - Per-section average energy (e.g. RMS)
      - Optional per-section vocal activity (0.0–1.0)

    Returns a list of SectionInference objects with type_soft + display_name.

    Args:
        audjust_sections: List of dicts with at least startMs, endMs, label.
        energy_per_section: Average energy value per section, aligned with audjust_sections.
        vocals_per_section: Optional vocal activity metrics per section.

    Returns:
        List of SectionInference objects with inferred section types.
    """

    n = len(audjust_sections)
    if n == 0:
        return []

    if len(energy_per_section) != n:
        raise ValueError("energy_per_section length must match audjust_sections length")
    if vocals_per_section is not None and len(vocals_per_section) != n:
        raise ValueError("vocals_per_section length must match audjust_sections length")

    # Step 1: construct basic sections with durations & positions
    sections_raw: List[dict] = []
    total_duration_sec = 0.0
    for i, section in enumerate(audjust_sections):
        start_ms = float(section.get("startMs", 0))
        end_ms = float(section.get("endMs", start_ms))
        label = int(section.get("label", -1))
        start_sec = max(0.0, start_ms / 1000.0)
        end_sec = max(start_sec, end_ms / 1000.0)
        duration_sec = max(0.0, end_sec - start_sec)
        total_duration_sec = max(total_duration_sec, end_sec)
        sections_raw.append(
            {
                "index": i,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": duration_sec,
                "label": label,
                "energy": float(energy_per_section[i]),
                "vocals": (
                    float(vocals_per_section[i]) if vocals_per_section is not None else None
                ),
            }
        )

    if total_duration_sec <= 0:
        total_duration_sec = sum(section["duration_sec"] for section in sections_raw)

    # Log raw sections from Audjust
    logger.info("Raw Audjust sections (%d total, %.1fs duration):", len(sections_raw), total_duration_sec)
    for seg in sections_raw:
        logger.info(
            "  %.1fs-%.1fs (%.1fs) | label=%d | energy=%.3f",
            seg["start_sec"],
            seg["end_sec"],
            seg["duration_sec"],
            seg["label"],
            seg["energy"],
        )

    # Step 2: cluster similar labels together
    # Audjust labels are 0-1000, closer numbers = more similar sections
    # We'll group labels within a threshold distance into the same cluster
    label_clusters = _cluster_similar_labels(
        [s["label"] for s in sections_raw],
        similarity_threshold=50,  # labels within 50 points are considered similar
    )
    
    # Map each section to its cluster representative
    for section in sections_raw:
        section["cluster_label"] = label_clusters[section["label"]]
    
    logger.info(
        "Label clustering: %d unique labels → %d clusters. Mapping: %s",
        len(set(s["label"] for s in sections_raw)),
        len(set(label_clusters.values())),
        {k: v for k, v in label_clusters.items() if k != v},  # show non-trivial mappings
    )

    # Step 3: group by cluster label and compute stats
    by_cluster: Dict[int, List[dict]] = defaultdict(list)
    for seg in sections_raw:
        by_cluster[seg["cluster_label"]].append(seg)

    cluster_stats = []
    for cluster_label, segs in by_cluster.items():
        occ = len(segs)
        total_dur = sum(s["duration_sec"] for s in segs)
        mean_energy = sum(s["energy"] for s in segs) / occ if occ else 0.0
        first_start = min(s["start_sec"] for s in segs)
        cluster_stats.append(
            {
                "label": cluster_label,
                "occ": occ,
                "total_dur": total_dur,
                "mean_energy": mean_energy,
                "first_start": first_start,
            }
        )

    # Log cluster statistics for debugging
    logger.info(
        "Cluster statistics: %d unique clusters, repetitions: %s",
        len(cluster_stats),
        {stat["label"]: stat["occ"] for stat in cluster_stats},
    )

    # Step 4: find chorus candidate (most repeated & energetic)
    # Only consider clusters that occur at least twice
    chorus_candidates = [stat for stat in cluster_stats if stat["occ"] >= 2]

    chorus_cluster = None
    if chorus_candidates:
        occ_norm = _normalize(stat["occ"] for stat in chorus_candidates)
        dur_norm = _normalize(stat["total_dur"] for stat in chorus_candidates)
        energy_norm = _normalize(stat["mean_energy"] for stat in chorus_candidates)

        best_score = -1.0
        best_cluster = None
        for idx, stat in enumerate(chorus_candidates):
            # Penalize sections whose first start is extremely early (< 8s)
            # but make it less aggressive
            early_penalty = 0.0
            if stat["first_start"] < 8.0:
                early_penalty = 0.2

            score = (
                0.5 * occ_norm[idx] +
                0.2 * dur_norm[idx] +
                0.3 * energy_norm[idx] -
                early_penalty
            )
            if score > best_score:
                best_score = score
                best_cluster = stat["label"]

        # Only accept if the score is reasonably high and occ >= 2
        # Lowered threshold from 0.2 to 0.15 to be more permissive
        if best_score > 0.15:
            chorus_cluster = best_cluster
            logger.info(
                "Detected chorus: cluster=%s, score=%.2f, occurrences=%d",
                best_cluster,
                best_score,
                next(s["occ"] for s in cluster_stats if s["label"] == best_cluster),
            )
        else:
            logger.warning(
                "No chorus detected. Best candidate score=%.2f (threshold=0.15), candidates=%d",
                best_score if best_score > -1 else 0.0,
                len(chorus_candidates),
            )
    else:
        logger.warning("No chorus candidates found (no clusters with ≥2 occurrences)")

    # Step 5: find verse-like clusters
    # verse-like: repeated clusters that are not chorus
    verse_clusters = set()
    for stat in cluster_stats:
        if stat["label"] == chorus_cluster:
            continue
        if stat["occ"] >= 2:
            verse_clusters.add(stat["label"])

    if verse_clusters:
        logger.info("Detected verse clusters: %s", verse_clusters)
    else:
        logger.warning("No verse clusters detected (no repeated non-chorus sections)")

    # Step 6: classify each segment with soft type
    inferred_sections: List[SectionInference] = []
    for segment in sections_raw:
        idx = segment["index"]
        label = segment["label"]
        cluster_label = segment["cluster_label"]
        center = (segment["start_sec"] + segment["end_sec"]) / 2.0
        pos_ratio = center / max(1e-6, total_duration_sec)
        base_type: SectionSoftType = "other"
        conf = 0.4  # baseline

        # chorus-like: most repeated & energetic section
        if chorus_cluster is not None and cluster_label == chorus_cluster:
            base_type = "chorus_like"
            conf = 0.7

        # verse-like: repeated sections that are not chorus
        elif cluster_label in verse_clusters:
            base_type = "verse_like"
            conf = 0.6

        # intro-like: early in song & not already classified as chorus/verse
        # Reduced from 0.2 to 0.15 to be more conservative with intro classification
        if base_type == "other" and pos_ratio < 0.15:
            base_type = "intro_like"
            conf = 0.6

        # outro-like: late in song & not already classified as chorus/verse
        # Increased from 0.8 to 0.85 to be more conservative with outro classification
        if base_type == "other" and pos_ratio > 0.85:
            base_type = "outro_like"
            conf = 0.6

        # bridge-like: unique cluster in middle region, not chorus/verse
        # Made the middle region narrower (0.35-0.75 instead of 0.3-0.8)
        # to reduce over-classification of bridges
        if (
            base_type == "other"
            and 0.35 < pos_ratio < 0.75
            and next(stat["occ"] for stat in cluster_stats if stat["label"] == cluster_label) == 1
        ):
            base_type = "bridge_like"
            conf = 0.5

        # if nothing fit, leave as "other" with baseline confidence
        # you could bump confidence using energy/vocals if desired

        inferred_sections.append(
            SectionInference(
                id=f"sec_{idx}",
                index=idx,
                start_sec=segment["start_sec"],
                end_sec=segment["end_sec"],
                duration_sec=segment["duration_sec"],
                label_raw=label,
                type_soft=base_type,
                confidence=conf,
                display_name="",  # filled later
            )
        )

    # Step 7: assign initial display names (Verse 1, Chorus 2, etc.)
    # Note: These will be reassigned after merging consecutive sections
    counters: Dict[SectionSoftType, int] = Counter()
    for section in inferred_sections:
        counters[section.type_soft] += 1
        ordinal = counters[section.type_soft]

        if section.type_soft == "chorus_like":
            section.display_name = f"Chorus {ordinal}"
        elif section.type_soft == "verse_like":
            section.display_name = f"Verse {ordinal}"
        elif section.type_soft == "intro_like":
            section.display_name = "Intro" if ordinal == 1 else f"Intro {ordinal}"
        elif section.type_soft == "outro_like":
            section.display_name = "Outro" if ordinal == 1 else f"Outro {ordinal}"
        elif section.type_soft == "bridge_like":
            section.display_name = "Bridge" if ordinal == 1 else f"Bridge {ordinal}"
        else:
            # fallback for "other": Section A/B/C...
            letter = chr(ord("A") + section.index)
            section.display_name = f"Section {letter}"

    # Sort back in chronological order
    inferred_sections.sort(key=lambda s: s.start_sec)

    # Log summary of inferred sections (before merging)
    type_counts = dict(counters)
    logger.info(
        "Section inference complete (before merging): %d total sections, types: %s",
        len(inferred_sections),
        type_counts,
    )

    # Step 8: Merge consecutive sections of the same type
    merged_sections = _merge_consecutive_sections(inferred_sections)

    # Log merged sections
    logger.info(
        "After merging consecutive sections: %d sections (reduced from %d)",
        len(merged_sections),
        len(inferred_sections),
    )

    # Log detailed section breakdown
    for section in merged_sections:
        logger.info(
            "  [%s] %.1fs-%.1fs (%.1fs) | raw_label=%d | conf=%.2f | %s",
            section.type_soft,
            section.start_sec,
            section.end_sec,
            section.duration_sec,
            section.label_raw,
            section.confidence,
            section.display_name,
        )

    return merged_sections

