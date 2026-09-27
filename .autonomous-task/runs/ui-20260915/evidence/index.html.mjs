
      import { $, setupPomodoro, setupVoice, setupWatchdog } from "./app.js";

      setupWatchdog();

      // Build clock-face tick marks (12 hour ticks only).
      const NS = "http://www.w3.org/2000/svg";
      const ticks = $("#clockTicks");
      for (let i = 0; i < 12; i += 1) {
        const a = (i / 12) * Math.PI * 2;
        const r1 = 137;
        const r2 = 145;
        const line = document.createElementNS(NS, "line");
        line.setAttribute("x1", String(150 + r1 * Math.sin(a)));
        line.setAttribute("y1", String(150 - r1 * Math.cos(a)));
        line.setAttribute("x2", String(150 + r2 * Math.sin(a)));
        line.setAttribute("y2", String(150 - r2 * Math.cos(a)));
        line.setAttribute("class", "tick major");
        ticks.appendChild(line);
      }

      setupPomodoro({
        displayEl: $("#timerDisplay"),
        modeEl: $("#timerMode"),
        startBtn: $("#startBtn"),
        resetBtn: $("#resetBtn"),
        skipBtn: $("#skipBtn"),
        sessionEl: $("#sessions"),
        badgeEl: $("#clockBadge"),
        progressEl: $("#clockProgress"),
        handEl: $("#clockHand"),
        faceEl: $(".clock-face"),
      });

      setupVoice({
        micBtn: $("#micBtn"),
        statusEl: $("#voiceStatus"),
        faceEl: $(".clock-face"),
      });
    