# Simple Testing Guide

A super simple guide to test the video app. No technical jargon, just easy steps.

---

## What You Need First

1. **Backend running**: Open terminal, go to `backend` folder, run:

   ```bash
   source venv/bin/activate
   python -m uvicorn app.main:app --reload
   ```

   Wait until you see "Uvicorn running on <http://127.0.0.1:8000>"

2. **Frontend running**: Open another terminal, go to `frontend` folder, run:

   ```bash
   npm run dev
   ```

   Wait until you see the frontend URL (usually <http://localhost:5173>)

3. **Test audio file**: Have an audio file ready (30-60 seconds is good)

4. **Browser**: Open <http://localhost:5173> in your browser

---

## The Simple Test Flow

Follow these steps in order. Each step should work before moving to the next.

### Step 1: Upload Audio (2 minutes)

**What to do:**

- Click "Upload" or drag your audio file
- Wait for upload to finish

**What should happen:**

- File uploads successfully
- You see a "Video Type" selector appear

**If it doesn't work:** Check that backend is running and you see no errors in
the browser console (press F12)

---

### Step 2: Choose Video Type (1 minute)

**What to do:**

- You'll see two options: "Full Length" or "Short Form"
- Click "Short Form"

**What should happen:**

- "Short Form" gets highlighted/selected
- A "Start Analysis" button appears

**If it doesn't work:** Try clicking the other option, then click "Short Form" again

---

### Step 3: Start Analysis (3-5 minutes)

**What to do:**

- Click "Start Analysis" button
- Wait (this takes a few minutes)

**What should happen:**

- You see a loading indicator
- After a few minutes, analysis completes
- A timeline with a waveform appears

**If it doesn't work:** Wait longer (analysis can take 3-5 minutes). Check
backend terminal for errors.

---

### Step 4: Select 30 Seconds of Audio (3 minutes)

**What to do:**

- You'll see a timeline with a waveform
- There are two markers (start and end)
- Drag the markers to select 30 seconds of audio
- Click the Play button to hear your selection
- Click "Continue with Selection" when happy

**What should happen:**

- Markers move when you drag them
- You can't select more than 30 seconds
- Audio plays when you click Play
- Selection saves when you click "Continue"

**If it doesn't work:** Make sure you selected "Short Form" in Step 2. Try refreshing the page.

---

### Step 5: Choose a Character (3-5 minutes)

**What to do:**

- You'll see a section to upload a character image
- Click "Choose Template" button (or "Upload Image" to use your own)
- A modal opens showing 4 characters
- Click on one character to select it
- OR upload your own image file (JPEG/PNG)

**What should happen:**

- Template modal opens and shows 4 characters
- When you click a character, it gets selected and modal closes
- You'll see both poses (Pose A and Pose B) displayed side-by-side
- Message appears: "We'll use your chosen template character for video generation"
- OR if you upload your own image, you see a preview
- Character selection UI is replaced with the selected template display

**If it doesn't work:** Make sure you're testing a "Short Form" video. Try
uploading a different image file or selecting a different template.

---

### Step 6: Generate Video Clips (5-10 minutes)

**What to do:**

- After selecting a character (template or custom), click "Generate Clips" button
- OR if you didn't select a character, you'll see a confirmation dialog asking if you want to proceed without a character image
- If you confirm without a character, the character selection UI will be hidden
- Wait (this takes several minutes)

**What should happen:**

- You see a loading indicator showing "Generating clip X of 8..."
- Individual clip statuses update in real-time (showing "Generating…" for active clips, "Awaiting generation" for queued clips)
- After several minutes, all clips are generated
- You see 8 video clips appear (for short-form videos)
- Character consistency is applied (same character appears in all clips if template/custom image was selected)

**If it doesn't work:** This step takes the longest. Wait at least 5-10 minutes.
Check backend terminal for progress. The UI should show real-time progress for each clip.

---

### Step 7: Compose Final Video (3-5 minutes)

**What to do:**

- Once all clips are completed, click "Compose Video" button
- Wait (this takes a few minutes)

**What should happen:**

- You see a loading indicator showing composition progress (e.g., "70%")
- After a few minutes, final video is ready
- The video player appears with the composed video
- Time display shows current playback time advancing (e.g., "0:05 / 0:30")
- Duration shows the selected 30-second duration, not the full file duration

**What to check in the final video:**

- Character looks consistent across all clips (same character throughout)
- Visual effects flash on the beat (flashes, color bursts, etc.)
- Video cuts happen on the beat (rhythmically correct)
- **CRITICAL:** Most clips should show a dancing figure/character
- **CRITICAL:** When a character appears, it should match the reference image you provided

**Known Issue:** Currently, most clips do not show a dancing figure, and when one does appear, it's not based on the reference image. This is being investigated.

**If it doesn't work:** Wait longer. Check backend terminal for errors.

---

## Quick Test (20 minutes)

If you want to test everything quickly:

1. Upload audio → Select "Short Form" → Start Analysis
2. Wait for analysis (3-5 min)
3. Select 30 seconds → Continue
4. Choose template character (or upload custom image) → See both poses displayed
5. Generate Clips → Wait (5-10 min)
6. Compose Video → Wait (3-5 min)
7. Watch final video → Check character consistency and beat sync

**All steps work?** ✅ Everything is working!

**Something broke?** See "Troubleshooting" below.

---

## Troubleshooting

### Problem: Upload doesn't work

- **Check:** Backend running? (See "What You Need First")
- **Try:** Refresh page, try again

### Problem: Analysis takes forever

- **Check:** Backend terminal for errors
- **Try:** Wait 5-10 minutes (analysis is slow)

### Problem: Can't select 30 seconds

- **Check:** Did you select "Short Form" in Step 2?
- **Try:** Refresh page, start over

### Problem: Character upload doesn't work

- **Check:** Using "Short Form" video type?
- **Try:** Use a different image file (JPEG or PNG)

### Problem: Clips don't generate

- **Check:** Backend terminal for errors
- **Try:** Wait longer (10+ minutes), check internet connection

### Problem: Final video looks wrong

- **Check:** Character should look the same in all clips
- **Check:** Visual effects should flash on beats
- **Check:** Cuts should happen on beats

---

## What Each Feature Does (Simple Explanation)

### Character Consistency

- **What it does:** Makes sure the same character appears in all video clips
- **How to test:** Choose a character, generate clips, check that character
  looks the same in all 6 clips

### Beat Sync

- **What it does:** Makes video effects and cuts happen on the beat of the music
- **How to test:** Watch final video, effects should flash on beats, cuts should
  be rhythmically correct

### 30-Second Selection

- **What it does:** Lets you pick exactly 30 seconds from your audio
- **How to test:** Drag markers on timeline, can't select more than 30 seconds

---

## Success Checklist

After testing, you should be able to say:

- [ ] I uploaded an audio file successfully
- [ ] I selected "Short Form" video type
- [ ] Analysis completed successfully
- [ ] I selected 30 seconds of audio
- [ ] I chose a character (template or custom)
- [ ] I saw both character poses displayed (if template selected)
- [ ] Clips generated successfully (6 clips)
- [ ] Final video composed successfully
- [ ] Character looks consistent in all clips
- [ ] Visual effects flash on beats
- [ ] Video cuts happen on beats

**All checked?** 🎉 Everything works!

---

## Need Help?

If something doesn't work:

1. **Check the backend terminal** - Look for error messages
2. **Check the browser console** - Press F12, look at Console tab for errors
3. **Try again** - Sometimes things just need a refresh
4. **Wait longer** - Some steps take 5-10 minutes

---

## That's It

This guide covers the basics. Follow the steps in order, and you'll test
everything. Keep it simple, take your time, and check each step before moving
to the next.

Good luck! 🎬
