# BeatDrop Feature Enhancement: Quick-Win Implementation Plan

This document outlines a simplified, high-impact plan for enhancing the BeatDrop AI video generation app, focusing on the quickest wins for **Character Consistency** and **Beat Synchronization**. The plan adheres to the constraint of using only models available via the **Replicate API** for video generation.

---

## 1. Quick-Win Feature Summary

The plan prioritizes the lowest-effort, highest-impact solutions for early validation.

| Priority | Feature | Technical Approach | Rationale & Quick Win Focus |
| :--- | :--- | :--- | :--- |
| **1. Character Consistency** | **Image Reference API** (Based on **Technical Exploration Option 1**) | **Multi-Step Workflow** using Replicate models: Generate a consistent character image, then use it as input for an Image-to-Video model. | **High-Impact Feature.** This is a core value proposition. The quick win is leveraging existing Replicate models, accepting a multi-step process as a necessary compromise. |
| **2. Beat Synchronization** | **Audio-Reactive Filters** (Based on **Technical Exploration Option 6**) | **FFmpeg Filter Injection on Beat.** Use the `beat_times` array to trigger simple, noticeable visual effects (color flash, zoom pulse) precisely on the beat. | **Lowest-Effort Sync.** This is a purely programmatic, post-generation step, creating the *perception* of beat-sync. |
| **3. Beat-Sync Enhancement** | **Prompt Engineering** (Based on **Technical Exploration Option 3**) | **Bias the prompt towards rhythmic motion.** Add phrases like "repetitive bouncing motion" to the base prompt. | **Zero-Code Quick Win.** Simple change to the prompt construction logic for immediate validation. |
| **4. Structural Sync** | **Multi-Shot Composition** (Based on **Technical Exploration Option 2**) | **Beat-Aligned Hard Cuts.** Ensure the transition between the 6 clips occurs precisely on a major beat. | **Medium-Effort, High-Impact.** Leverages the existing clip-based structure for rhythmic cuts. |

---

## 2. Character Consistency: Multi-Step Workflow (Replicate Constraint)

The constraint to use Replicate models necessitates a shift from a single, high-fidelity API call to a multi-step process to achieve character consistency.

### 2.1. Implementation Steps

The `generate_video_clip` job must be modified to execute the following sequence:

| Step | Component | Description | Replicate Model Example |
| :--- | :--- | :--- | :--- |
| **1. Image Interrogation** | Back-End (Python) | Use a multimodal LLM (e.g., `gpt-4.1-mini`) to generate a highly detailed, descriptive prompt from the user's uploaded reference image. | N/A (Standard LLM API) |
| **2. Consistent Image Generation** | Replicate API Call | Use the Interrogated Prompt and the user's image as input to generate a new, highly consistent character image. | `stability-ai/stable-diffusion-xl` with ControlNet/IP-Adapter |
| **3. Video Generation (6 Clips)** | Replicate API Call | Use the **Consistent Image** from Step 2 as the Image Input for the Image-to-Video model, along with the Final Constructed Prompt. This step is repeated for all 6 clips. | `google/veo-3.1` or `luma/ray` |

**Crucial Caveat:** This approach is a **compromise**. While the input image is consistent, the Image-to-Video model may still introduce visual drift across the 6 separate generations. Extensive testing will be required to find the best combination of Replicate models that minimizes this drift.

---

## 3. Beat Synchronization: Programmatic Quick Wins

These post-processing steps are independent of the video generation API and rely on the existing FFmpeg composition pipeline.

### 3.1. Prompt Engineering (Technical Exploration Option 3)

The base prompt template (as described in the PRD) should be modified to bias the AI model toward rhythmic motion.

*   **Modification:** The prompt should include phrases like: "**repetitive bouncing motion, pulsing to a 128 BPM tempo**" to encourage a more rhythmic output from the AI model.

### 3.2. Audio-Reactive FFmpeg Filters (Technical Exploration Option 6)

This occurs in the `compose_final_video` job after all clips are downloaded and concatenated.

*   **Input:** The concatenated video stream and the `beat_times` array from `song_analyses`.
*   **Strategy:** Use FFmpeg's `select` and `geq` filters to apply a simple, noticeable visual effect (e.g., a white flash or color burst) for a single frame at the exact timestamp of every major beat. This provides a strong, perfectly timed visual cue.

**Example FFmpeg Filter Logic:**

The logic involves creating a boolean expression based on the `beat_times` array to trigger a filter (like `geq` for a flash) only when the current frame's timestamp is within a small window of a beat.

### 3.3. Structural Sync (Technical Exploration Option 2)

*   **Modification:** In the `compose_final_video` job, the cut points between the 6 clips must be aligned to the nearest major beat in the `beat_times` array. This ensures the most jarring visual transition (the cut) is rhythmically correct.

---

## 4. Appendix: OpenCV Motion Analysis and Selective Time-Stretching (Future Work)

This section details the most advanced, high-effort approach for achieving true beat synchronization, as outlined in **Technical Exploration Approach 1**. This method should be considered **Future Work** and implemented only after the quick-win strategies have been fully deployed and validated.

### 4.1. Goal: True Motion Synchronization

The objective is to programmatically align the peak moments of motion within the AI-generated video clips to the precise timestamps of the musical beats (`beat_times`).

### 4.2. Technical Approach: Post-Generation Manipulation

This approach uses computer vision to analyze the generated video and then uses video processing tools (FFmpeg) to manipulate the playback speed of specific segments.

#### Stage 1: Motion Analysis with OpenCV

The core is to quantify "motion" using **Optical Flow** (specifically `cv2.calcOpticalFlowFarneback`) to create a **Motion Intensity Signal** over time. This signal is then smoothed and normalized to highlight significant movements.

#### Stage 2: Peak Detection and Alignment Calculation

*   **Peak Detection:** Use `scipy.signal.find_peaks` to identify the timestamps of the most prominent motion peaks.
*   **Alignment:** For each motion peak, find the closest beat timestamp in the `beat_times` array.
*   **Calculation:** Calculate the required `stretch_factor` (speed change) to move the motion peak to the target beat timestamp.

$$
\text{Stretch Factor} = \frac{\text{Original Duration}}{\text{Target Duration}} = \frac{\text{Motion Peak Time}}{\text{Target Beat Time}}
$$

#### Stage 3: Video Manipulation with FFmpeg

*   **Filter:** Use FFmpeg's `setpts` filter to apply variable speed changes to the video segments that require adjustment.
*   **Process:** The video is split into segments, each segment is processed with the appropriate `setpts` value, and all segments are then concatenated back together.

This method offers the highest quality synchronization but requires significant development time, testing, and computational resources. It is the ultimate goal for beat-sync precision.
