// Queue Dashboard Handler for YTDL

function stripAnsi(str) {
  if (!str) return "—";
  return String(str).replace(/\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])/g, "").trim() || "—";
}

function isJobDone(job) {
  if (!job) return true;
  const s = String(job.stage || "").toUpperCase();
  const m = String(job.status_msg || "").toUpperCase();
  return s === "COMPLETED" || s === "FAILED" || s === "CANCELLED" || m === "COMPLETED";
}

export function renderQueueDashboard(jobs) {
  const listEl = document.getElementById("queue-list");
  const badgeEl = document.getElementById("queue-status-badge");

  if (!jobs || jobs.length === 0) {
    listEl.innerHTML = `
      <div class="empty-queue-msg">
        <span class="empty-icon">📂</span>
        <p>No active download jobs. Extract a media URL above to start downloading.</p>
      </div>
    `;
    badgeEl.textContent = "IDLE";
    badgeEl.classList.remove("active");
    return;
  }

  const activeJobs = jobs.filter(j => !isJobDone(j));
  if (activeJobs.length > 0) {
    badgeEl.textContent = `ACTIVE (${activeJobs.length})`;
    badgeEl.classList.add("active");
  } else {
    badgeEl.textContent = "IDLE";
    badgeEl.classList.remove("active");
  }

  listEl.innerHTML = "";
  jobs.forEach(job => {
    const card = document.createElement("div");
    card.className = "job-card";
    const isVideoStage = job.stage === "VIDEO_DOWNLOAD" || job.stage === "Video Stream Download";
    const isAudioStage = job.stage === "AUDIO_DOWNLOAD" || job.stage === "Audio Stream Download";
    const isMergeStage = job.stage === "MERGING" || job.stage === "Merging";
    const isConvertStage = job.stage === "CONVERTING" || job.stage === "Converting";
    const isCompletedStage = job.stage === "COMPLETED" || job.stage === "Completed" || job.status_msg === "Completed";
    const isFailedStage = job.stage === "FAILED" || job.stage === "Failed";
    const isCancelledStage = job.stage === "CANCELLED" || job.stage === "Cancelled";

    if (isCompletedStage || isCancelledStage) {
      return;
    }

    if (!isFailedStage) {
      card.classList.add("active");
    }

    const isVideoDone = (job.video_progress >= 1.0) || isMergeStage || isConvertStage || isCompletedStage;
    const isAudioDone = (job.audio_progress >= 1.0) || isMergeStage || isConvertStage || isCompletedStage;
    const isMergeDone = (job.merge_progress >= 1.0) || isConvertStage || isCompletedStage;
    const isConvertDone = (job.convert_progress >= 1.0) || isCompletedStage;

    const isVideoActive = !isVideoDone && (job.download_mode !== "audio_only") && (isVideoStage || isAudioStage || (job.video_progress > 0 && job.video_progress < 1.0));
    const isAudioActive = !isAudioDone && (job.download_mode !== "video_only") && (isAudioStage || isVideoStage || (job.audio_progress > 0 && job.audio_progress < 1.0));
    const isMergeActive = !isMergeDone && isMergeStage;
    const isConvertActive = !isConvertDone && isConvertStage;

    let overallProg = 0;
    let speedStr = "—";
    let etaStr = "—";

    if (isCompletedStage) {
      overallProg = 100;
      speedStr = "Done";
      etaStr = "00:00";
    } else if (job.download_mode === "audio_only") {
      if (isConvertStage) {
        overallProg = 50 + ((job.convert_progress || 0) * 50);
        speedStr = "FFmpeg";
        etaStr = "00:05";
      } else {
        overallProg = (job.audio_progress || 0) * 50;
        speedStr = stripAnsi(job.audio_speed);
        etaStr = stripAnsi(job.audio_eta);
      }
    } else if (job.download_mode === "video_only") {
      if (isConvertStage) {
        overallProg = 50 + ((job.convert_progress || 0) * 50);
        speedStr = "FFmpeg";
        etaStr = "00:05";
      } else {
        overallProg = (job.video_progress || 0) * 50;
        speedStr = stripAnsi(job.video_speed);
        etaStr = stripAnsi(job.video_eta);
      }
    } else {
      // 4 divisions (25, 25, 25, 25): Audio 25%, Video 25% (total 50% when both finish), Merging 25%, Converting 25%
      const vidContrib = (job.video_progress || 0) * 25;
      const audContrib = (job.audio_progress || 0) * 25;
      if (isMergeStage) {
        overallProg = 50 + ((job.merge_progress || 0) * 25);
        speedStr = "Fast Mux";
        etaStr = "00:02";
      } else if (isConvertStage) {
        overallProg = 75 + ((job.convert_progress || 0) * 25);
        speedStr = "FFmpeg";
        etaStr = "00:05";
      } else {
        overallProg = vidContrib + audContrib;
        if (isVideoStage && !isVideoDone) {
          speedStr = stripAnsi(job.video_speed);
          etaStr = stripAnsi(job.video_eta);
        } else if (isAudioStage && !isAudioDone) {
          speedStr = stripAnsi(job.audio_speed);
          etaStr = stripAnsi(job.audio_eta);
        } else {
          speedStr = stripAnsi(job.video_speed || job.audio_speed);
          etaStr = stripAnsi(job.video_eta || job.audio_eta);
        }
      }
    }

    card.innerHTML = `
      <div class="job-header">
        <span class="job-title">${job.title}</span>
        <span class="job-mode-badge">${job.download_mode || "video_audio"}${isCompletedStage ? "" : ` &bull; ${job.stage}`}</span>
      </div>

      <div class="stages-row">
        <div class="stage-pill ${isVideoActive ? 'active' : ''} ${isVideoDone ? 'done' : ''}">
          Stage 1: Video (${Math.round(job.video_progress * 100)}%)
        </div>
        <div class="stage-pill ${isAudioActive ? 'active' : ''} ${isAudioDone ? 'done' : ''}">
          Stage 2: Audio (${Math.round(job.audio_progress * 100)}%)
        </div>
        <div class="stage-pill ${isMergeActive ? 'active' : ''} ${isMergeDone ? 'done' : ''}">
          Stage 3: Merge (${Math.round(job.merge_progress * 100)}%)
        </div>
        <div class="stage-pill ${isConvertActive ? 'active' : ''} ${isConvertDone ? 'done' : ''}">
          Stage 4: Convert (${Math.round(job.convert_progress * 100)}%)
        </div>
      </div>

      <div class="progress-wrapper">
        <div class="progress-info">
          <span>${job.status_msg || job.stage}</span>
          <span>Progress: ${Math.round(overallProg)}% &nbsp;|&nbsp; Speed: ${speedStr} &nbsp;|&nbsp; ETA: ${etaStr}</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width: ${Math.round(overallProg)}%; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);"></div>
        </div>
      </div>
    `;

    listEl.appendChild(card);
  });

  if (listEl.children.length === 0 && jobs.length > 0) {
    const allDoneCard = document.createElement("div");
    allDoneCard.className = "empty-queue-msg";
    allDoneCard.style.padding = "24px";
    allDoneCard.innerHTML = `
      <span class="empty-icon" style="font-size: 2.4rem; display: block; margin-bottom: 10px;">✅</span>
      <p style="font-size: 1.05rem; font-weight: 600; color: var(--text-main);">${jobs.length > 1 ? `All ${jobs.length} downloads` : "Download"} completed successfully!</p>
    `;
    listEl.appendChild(allDoneCard);
  }

  if (jobs.length > 1) {
    let totalProgressSum = 0;
    let completedCount = 0;
    jobs.forEach(job => {
      let p = 0;
      if (job.stage === "VIDEO_DOWNLOAD" || job.stage === "Video Stream Download") p = job.video_progress * 40;
      else if (job.stage === "AUDIO_DOWNLOAD" || job.stage === "Audio Stream Download") p = 40 + job.audio_progress * 40;
      else if (job.stage === "MERGING" || job.stage === "Merging") p = 80 + job.merge_progress * 10;
      else if (job.stage === "CONVERTING" || job.stage === "Converting") p = 90 + job.convert_progress * 10;
      else if (job.stage === "COMPLETED" || job.stage === "Completed" || job.status_msg === "Completed") {
        p = 100;
        completedCount++;
      }
      totalProgressSum += p;
    });
    const batchAvg = Math.round(totalProgressSum / jobs.length);

    const batchCard = document.createElement("div");
    batchCard.className = "job-card";
    batchCard.style.border = "1px solid var(--accent-cyan)";
    batchCard.style.background = "rgba(0, 206, 201, 0.08)";
    batchCard.style.marginTop = "20px";

    batchCard.innerHTML = `
      <div class="job-header" style="margin-bottom: 12px;">
        <span class="job-title" style="color: var(--accent-cyan); font-weight: 700;">
          📦 Overall Batch Progress (${completedCount}/${jobs.length} Videos Completed)
        </span>
        <span class="job-mode-badge">${batchAvg}% Complete</span>
      </div>
      <div class="progress-wrapper">
        <div class="progress-info">
          <span>Total Batch Processing</span>
          <span>${completedCount} of ${jobs.length} completed (${batchAvg}%)</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width: ${batchAvg}%; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1); background: var(--accent-cyan);"></div>
        </div>
      </div>
    `;
    listEl.appendChild(batchCard);
  }
}
