/**
 * IRONPULSE - Smart Physical Training System
 * Pure Frontend Architecture (Vanilla JS)
 * No Backend / No External API Dependencies
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // =========================================================================
  // 1. Initial State & Storage Management
  // =========================================================================
  const STORAGE_KEY = 'ironpulse_athlete_profile';

  const defaultProfile = {
    gender: 'Male',
    focusArea: ['Chest', 'Arms'],
    goals: ['Build Muscle'],
    motivation: ['Improve Health'],
    pushupLevel: 'Beginner',
    activityLevel: 'Moderately Active',
    weeklyTrainingDays: 3,
    firstDay: 'Monday',
    weight: 68,
    weightUnit: 'KG',
    height: 175,
    heightUnit: 'CM',
    avatarUrl: 'assets/male.png',
    customImage: null,
    streak: 5,
    completedWorkouts: 8,
    totalTargetWorkouts: 12,
    consistency: 78,
    feedbackGiven: false
  };

  let athleteProfile = loadProfile();

  function loadProfile() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return { ...defaultProfile, ...JSON.parse(saved) };
      }
    } catch (e) {
      console.warn('LocalStorage error:', e);
    }
    return { ...defaultProfile };
  }

  function saveProfile() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(athleteProfile));
    } catch (e) {
      console.warn('Failed to save to localStorage:', e);
    }
  }

  // =========================================================================
  // 2. Audio Synthesizer (Pure Web Audio API - No External Sound Files)
  // =========================================================================
  const AudioEngine = {
    ctx: null,
    init() {
      if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioCtx();
      }
    },
    playTone(freq = 440, type = 'sine', duration = 0.15) {
      try {
        this.init();
        if (!this.ctx) return;
        if (this.ctx.state === 'suspended') {
          this.ctx.resume();
        }
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
        gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + duration);
      } catch (err) {
        // Audio policy or unsupported
      }
    },
    playBeep() {
      this.playTone(600, 'sine', 0.1);
    },
    playSuccess() {
      setTimeout(() => this.playTone(523.25, 'triangle', 0.12), 0);
      setTimeout(() => this.playTone(659.25, 'triangle', 0.15), 100);
      setTimeout(() => this.playTone(783.99, 'triangle', 0.25), 200);
    }
  };

  // =========================================================================
  // 3. UI Toast Alerts
  // =========================================================================
  function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <i class="fa-solid fa-circle-check"></i>
      <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 4000);
  }

  // =========================================================================
  // 4. Header & Navigation Behaviors
  // =========================================================================
  const siteHeader = document.getElementById('siteHeader');
  const hamburgerBtn = document.getElementById('hamburgerBtn');
  const mobileDrawer = document.getElementById('mobileDrawer');
  const mobileOverlay = document.getElementById('mobileOverlay');
  const drawerCloseBtn = document.getElementById('drawerCloseBtn');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      siteHeader.classList.add('scrolled');
    } else {
      siteHeader.classList.remove('scrolled');
    }
  });

  function toggleMobileMenu(open) {
    if (open) {
      mobileDrawer.classList.add('open');
      mobileOverlay.classList.add('active');
    } else {
      mobileDrawer.classList.remove('open');
      mobileOverlay.classList.remove('active');
    }
  }

  if (hamburgerBtn) hamburgerBtn.addEventListener('click', () => toggleMobileMenu(true));
  if (drawerCloseBtn) drawerCloseBtn.addEventListener('click', () => toggleMobileMenu(false));
  if (mobileOverlay) mobileOverlay.addEventListener('click', () => toggleMobileMenu(false));

  document.querySelectorAll('.mobile-link').forEach(link => {
    link.addEventListener('click', () => toggleMobileMenu(false));
  });

  // =========================================================================
  // 5. Multi-Step Assessment Modal Logic (Steps 1 to 9)
  // =========================================================================
  const assessmentModal = document.getElementById('assessmentModal');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const stepPrevBtn = document.getElementById('stepPrevBtn');
  const stepNextBtn = document.getElementById('stepNextBtn');
  const stepSkipBtn = document.getElementById('stepSkipBtn');
  const modalStepCounter = document.getElementById('modalStepCounter');
  const modalProgressBar = document.getElementById('modalProgressBar');

  const navGetStartedBtn = document.getElementById('navGetStartedBtn');
  const heroStartBtn = document.getElementById('heroStartBtn');
  const mobileGetStartedBtn = document.getElementById('mobileGetStartedBtn');
  const dashRetakeAssessmentBtn = document.getElementById('dashRetakeAssessmentBtn');

  let currentStep = 1;
  const totalSteps = 9;

  function openAssessment() {
    currentStep = 1;
    updateStepUI();
    assessmentModal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeAssessment() {
    assessmentModal.classList.remove('active');
    document.body.style.overflow = '';
  }

  [navGetStartedBtn, heroStartBtn, mobileGetStartedBtn, dashRetakeAssessmentBtn].forEach(btn => {
    if (btn) btn.addEventListener('click', (e) => {
      e.preventDefault();
      toggleMobileMenu(false);
      openAssessment();
    });
  });

  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeAssessment);

  function updateStepUI() {
    // Hide all steps
    document.querySelectorAll('.assessment-step').forEach(step => {
      step.style.display = 'none';
    });

    // Show current step
    const activeStepEl = document.getElementById(`step${currentStep}`);
    if (activeStepEl) activeStepEl.style.display = 'block';

    // Update Progress Indicator & Bar
    if (modalStepCounter) modalStepCounter.textContent = `Step ${currentStep} of ${totalSteps}`;
    if (modalProgressBar) {
      const pct = Math.round((currentStep / totalSteps) * 100);
      modalProgressBar.style.width = `${pct}%`;
    }

    // Prev Button Visibility
    if (stepPrevBtn) {
      stepPrevBtn.style.visibility = currentStep > 1 ? 'visible' : 'hidden';
    }

    // Skip Button Visibility (Only Step 9 has skip)
    if (stepSkipBtn) {
      stepSkipBtn.style.display = currentStep === 9 ? 'inline-flex' : 'none';
    }

    // Next Button Text
    if (stepNextBtn) {
      if (currentStep === totalSteps) {
        stepNextBtn.innerHTML = `BUILD MY PLAN <i class="fa-solid fa-wand-magic-sparkles"></i>`;
      } else {
        stepNextBtn.innerHTML = `NEXT <i class="fa-solid fa-arrow-right"></i>`;
      }
    }

    // Sync input fields with current athlete profile values
    syncFormInputsWithProfile();
  }

  function syncFormInputsWithProfile() {
    // Step 1: Gender
    const maleCard = document.getElementById('genderCardMale');
    const femaleCard = document.getElementById('genderCardFemale');
    if (maleCard && femaleCard) {
      maleCard.classList.toggle('selected', athleteProfile.gender === 'Male');
      femaleCard.classList.toggle('selected', athleteProfile.gender === 'Female');
    }

    // Step 2: Focus Area
    document.querySelectorAll('#step2 .multi-card').forEach(card => {
      const val = card.getAttribute('data-val');
      card.classList.toggle('selected', athleteProfile.focusArea.includes(val));
    });

    // Step 3: Goals
    document.querySelectorAll('#step3 .multi-card').forEach(card => {
      const val = card.getAttribute('data-val');
      card.classList.toggle('selected', athleteProfile.goals.includes(val));
    });

    // Step 4: Motivation
    document.querySelectorAll('#step4 .multi-card').forEach(card => {
      const val = card.getAttribute('data-val');
      card.classList.toggle('selected', athleteProfile.motivation.includes(val));
    });

    // Step 5: Push-up Level
    document.querySelectorAll('#step5 .single-card').forEach(card => {
      const val = card.getAttribute('data-val');
      card.classList.toggle('selected', athleteProfile.pushupLevel === val);
    });

    // Step 6: Activity Level
    document.querySelectorAll('#step6 .single-card').forEach(card => {
      const val = card.getAttribute('data-val');
      card.classList.toggle('selected', athleteProfile.activityLevel === val);
    });

    // Step 7: Weekly days & Start Day
    document.querySelectorAll('.day-num-btn').forEach(btn => {
      const days = parseInt(btn.getAttribute('data-days'), 10);
      btn.classList.toggle('active', athleteProfile.weeklyTrainingDays === days);
    });
    const daysDisplay = document.getElementById('daysCountDisplay');
    if (daysDisplay) daysDisplay.textContent = `${athleteProfile.weeklyTrainingDays} DAYS / WEEK`;

    document.querySelectorAll('.start-day-pill').forEach(pill => {
      const day = pill.getAttribute('data-day');
      pill.classList.toggle('active', athleteProfile.firstDay === day);
    });

    // Step 8: Body details
    const weightInput = document.getElementById('weightInput');
    const heightInput = document.getElementById('heightInput');
    if (weightInput) weightInput.value = athleteProfile.weight;
    if (heightInput) heightInput.value = athleteProfile.height;
  }

  // --- Step 1: Gender Selection Handling ---
  document.querySelectorAll('.gender-card').forEach(card => {
    card.addEventListener('click', () => {
      AudioEngine.playBeep();
      const val = card.getAttribute('data-val');
      athleteProfile.gender = val;
      athleteProfile.avatarUrl = val === 'Female' ? 'assets/female.png' : 'assets/male.png';
      document.querySelectorAll('.gender-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
    });
  });

  // --- Step 2, 3, 4: Multi-select Cards Handling ---
  function setupMultiSelect(containerSelector, profileProperty, defaultFallback) {
    document.querySelectorAll(`${containerSelector} .multi-card`).forEach(card => {
      card.addEventListener('click', () => {
        AudioEngine.playBeep();
        const val = card.getAttribute('data-val');
        const list = athleteProfile[profileProperty];
        const idx = list.indexOf(val);
        if (idx > -1) {
          // Do not allow empty array
          if (list.length > 1) {
            list.splice(idx, 1);
            card.classList.remove('selected');
          } else {
            showToast('Please keep at least one option selected', 'warning');
          }
        } else {
          list.push(val);
          card.classList.add('selected');
        }
      });
    });
  }

  setupMultiSelect('#step2', 'focusArea', ['Full Body']);
  setupMultiSelect('#step3', 'goals', ['Build Muscle']);
  setupMultiSelect('#step4', 'motivation', ['Improve Health']);

  // --- Step 5 & 6: Single-select Cards Handling ---
  function setupSingleSelect(containerSelector, profileProperty) {
    document.querySelectorAll(`${containerSelector} .single-card`).forEach(card => {
      card.addEventListener('click', () => {
        AudioEngine.playBeep();
        const val = card.getAttribute('data-val');
        athleteProfile[profileProperty] = val;
        document.querySelectorAll(`${containerSelector} .single-card`).forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
      });
    });
  }

  setupSingleSelect('#step5', 'pushupLevel');
  setupSingleSelect('#step6', 'activityLevel');

  // --- Step 7: Training Days & Starting Day Handling ---
  document.querySelectorAll('.day-num-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      AudioEngine.playBeep();
      const days = parseInt(btn.getAttribute('data-days'), 10);
      athleteProfile.weeklyTrainingDays = days;
      document.querySelectorAll('.day-num-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const daysDisplay = document.getElementById('daysCountDisplay');
      if (daysDisplay) daysDisplay.textContent = `${days} DAYS / WEEK`;
    });
  });

  document.querySelectorAll('.start-day-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      AudioEngine.playBeep();
      const day = pill.getAttribute('data-day');
      athleteProfile.firstDay = day;
      document.querySelectorAll('.start-day-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
    });
  });

  // --- Step 8: Body Details & Frontend Validation ---
  const weightInput = document.getElementById('weightInput');
  const heightInput = document.getElementById('heightInput');
  const weightError = document.getElementById('weightError');
  const heightError = document.getElementById('heightError');

  // Unit toggles
  document.querySelectorAll('#weightUnitToggle .unit-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const unit = btn.getAttribute('data-unit');
      athleteProfile.weightUnit = unit;
      document.querySelectorAll('#weightUnitToggle .unit-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Auto convert weight value
      const val = parseFloat(weightInput.value);
      if (!isNaN(val)) {
        if (unit === 'LBS') {
          weightInput.value = Math.round(val * 2.20462);
        } else {
          weightInput.value = Math.round(val / 2.20462);
        }
      }
    });
  });

  document.querySelectorAll('#heightUnitToggle .unit-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const unit = btn.getAttribute('data-unit');
      athleteProfile.heightUnit = unit;
      document.querySelectorAll('#heightUnitToggle .unit-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  function validateStep8() {
    let isValid = true;
    const w = parseFloat(weightInput.value);
    const h = parseFloat(heightInput.value);

    // Weight validation (30 to 250 kg or 66 to 550 lbs)
    const minW = athleteProfile.weightUnit === 'KG' ? 30 : 66;
    const maxW = athleteProfile.weightUnit === 'KG' ? 250 : 550;

    if (isNaN(w) || w < minW || w > maxW) {
      weightInput.classList.add('error');
      weightError.classList.add('visible');
      isValid = false;
    } else {
      weightInput.classList.remove('error');
      weightError.classList.remove('visible');
      athleteProfile.weight = w;
    }

    // Height validation (90 to 250 cm)
    if (isNaN(h) || h < 90 || h > 250) {
      heightInput.classList.add('error');
      heightError.classList.add('visible');
      isValid = false;
    } else {
      heightInput.classList.remove('error');
      heightError.classList.remove('visible');
      athleteProfile.height = h;
    }

    return isValid;
  }

  // --- Step 9: Optional Body Image Upload (FileReader Frontend Preview) ---
  const dropzoneArea = document.getElementById('dropzoneArea');
  const imageFileInput = document.getElementById('imageFileInput');
  const dropzoneDefaultUI = document.getElementById('dropzoneDefaultUI');
  const dropzonePreviewContainer = document.getElementById('dropzonePreviewContainer');
  const uploadedImgPreview = document.getElementById('uploadedImgPreview');
  const removeImageBtn = document.getElementById('removeImageBtn');

  if (dropzoneArea && imageFileInput) {
    dropzoneArea.addEventListener('click', (e) => {
      if (e.target !== removeImageBtn && !removeImageBtn.contains(e.target)) {
        imageFileInput.click();
      }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzoneArea.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzoneArea.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzoneArea.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzoneArea.classList.remove('dragover');
      });
    });

    dropzoneArea.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        processUploadedImage(files[0]);
      }
    });

    imageFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        processUploadedImage(e.target.files[0]);
      }
    });
  }

  function processUploadedImage(file) {
    if (!file.type.match('image.*')) {
      showToast('Please select a valid image file (JPG or PNG)', 'warning');
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      athleteProfile.customImage = event.target.result;
      athleteProfile.avatarUrl = event.target.result;
      if (uploadedImgPreview) uploadedImgPreview.src = event.target.result;
      if (dropzoneDefaultUI) dropzoneDefaultUI.style.display = 'none';
      if (dropzonePreviewContainer) dropzonePreviewContainer.classList.add('active');
      showToast('Workout image loaded successfully!');
    };
    reader.readAsDataURL(file);
  }

  if (removeImageBtn) {
    removeImageBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      athleteProfile.customImage = null;
      athleteProfile.avatarUrl = athleteProfile.gender === 'Female' ? 'assets/female.png' : 'assets/male.png';
      if (imageFileInput) imageFileInput.value = '';
      if (dropzoneDefaultUI) dropzoneDefaultUI.style.display = 'block';
      if (dropzonePreviewContainer) dropzonePreviewContainer.classList.remove('active');
    });
  }

  // --- Step Navigation Buttons (Prev / Next / Skip) ---
  if (stepPrevBtn) {
    stepPrevBtn.addEventListener('click', () => {
      if (currentStep > 1) {
        currentStep--;
        updateStepUI();
      }
    });
  }

  if (stepNextBtn) {
    stepNextBtn.addEventListener('click', () => {
      // Validate step 8
      if (currentStep === 8) {
        if (!validateStep8()) {
          AudioEngine.playTone(300, 'sawtooth', 0.2);
          return;
        }
      }

      if (currentStep < totalSteps) {
        currentStep++;
        updateStepUI();
      } else {
        // Finished all steps -> Close assessment and trigger Analysis screen
        closeAssessment();
        saveProfile();
        triggerFitnessAnalysis();
      }
    });
  }

  if (stepSkipBtn) {
    stepSkipBtn.addEventListener('click', () => {
      closeAssessment();
      saveProfile();
      triggerFitnessAnalysis();
    });
  }

  // =========================================================================
  // 6. Fitness Analysis Screen Simulation (Step 15)
  // =========================================================================
  const analysisOverlay = document.getElementById('analysisOverlay');
  const analysisCircleMeter = document.getElementById('analysisCircleMeter');
  const analysisPercentText = document.getElementById('analysisPercentText');

  function triggerFitnessAnalysis() {
    if (!analysisOverlay) return;

    analysisOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Reset items
    for (let i = 1; i <= 4; i++) {
      const item = document.getElementById(`analysisStep${i}`);
      if (item) {
        item.classList.remove('active', 'completed');
      }
    }

    let progress = 0;
    const circumference = 440; // 2 * PI * 70 approx 440

    const interval = setInterval(() => {
      progress += 2;
      if (progress > 100) progress = 100;

      // Update circular meter
      const offset = circumference - (progress / 100) * circumference;
      if (analysisCircleMeter) analysisCircleMeter.style.strokeDashoffset = offset;
      if (analysisPercentText) analysisPercentText.textContent = `${progress}%`;

      // Sequential checklist activation
      if (progress >= 20) activateAnalysisStep(1);
      if (progress >= 45) { completeAnalysisStep(1); activateAnalysisStep(2); }
      if (progress >= 70) { completeAnalysisStep(2); activateAnalysisStep(3); }
      if (progress >= 90) { completeAnalysisStep(3); activateAnalysisStep(4); }

      if (progress >= 100) {
        clearInterval(interval);
        completeAnalysisStep(4);
        AudioEngine.playSuccess();

        setTimeout(() => {
          analysisOverlay.classList.remove('active');
          document.body.style.overflow = '';
          showToast('Your personalized workout plan is ready!');
          renderDashboard();
          activateDashboardView();
        }, 700);
      }
    }, 45);
  }

  function activateAnalysisStep(stepNum) {
    const el = document.getElementById(`analysisStep${stepNum}`);
    if (el && !el.classList.contains('active')) {
      el.classList.add('active');
      AudioEngine.playBeep();
    }
  }

  function completeAnalysisStep(stepNum) {
    const el = document.getElementById(`analysisStep${stepNum}`);
    if (el) el.classList.add('completed');
  }

  // =========================================================================
  // 7. Dashboard Rendering & Workout Personalization (Steps 16, 17, 18, 21)
  // =========================================================================
  const dashboardSection = document.getElementById('dashboardSection');
  const navDashboardLink = document.getElementById('navDashboardLink');
  const mobileDashboardLink = document.getElementById('mobileDashboardLink');

  function activateDashboardView() {
    if (dashboardSection) {
      dashboardSection.classList.add('active');
      dashboardSection.scrollIntoView({ behavior: 'smooth' });
    }
    if (navDashboardLink) navDashboardLink.style.display = 'inline-block';
    if (mobileDashboardLink) mobileDashboardLink.style.display = 'block';
  }

  function renderDashboard() {
    // 1. User Header & Badges
    const userAvatar = document.getElementById('dashboardUserAvatar');
    if (userAvatar) userAvatar.src = athleteProfile.avatarUrl || 'assets/male.png';

    const greeting = document.getElementById('dashboardGreeting');
    if (greeting) greeting.textContent = `Welcome, ${athleteProfile.gender === 'Female' ? 'Athlete' : 'Champion'}`;

    const badgeFocus = document.getElementById('badgeFocus');
    if (badgeFocus) badgeFocus.textContent = `Focus: ${athleteProfile.focusArea.join(', ')}`;

    const badgeGoal = document.getElementById('badgeGoal');
    if (badgeGoal) badgeGoal.textContent = `Goal: ${athleteProfile.goals.join(', ')}`;

    const badgeLevel = document.getElementById('badgeLevel');
    if (badgeLevel) badgeLevel.textContent = `Level: ${athleteProfile.pushupLevel}`;

    // 2. Statistics
    const statTrainingDays = document.getElementById('statTrainingDays');
    if (statTrainingDays) statTrainingDays.textContent = athleteProfile.weeklyTrainingDays;

    const statTotalExercises = document.getElementById('statTotalExercises');
    const totalEx = athleteProfile.weeklyTrainingDays * 4;
    if (statTotalExercises) statTotalExercises.textContent = totalEx;

    const statConsistency = document.getElementById('statConsistency');
    if (statConsistency) statConsistency.textContent = `${athleteProfile.consistency}%`;

    const streakVal = document.getElementById('streakCounterVal');
    if (streakVal) streakVal.textContent = athleteProfile.streak;

    const completedRatio = document.getElementById('completedRatioText');
    if (completedRatio) completedRatio.textContent = `${athleteProfile.completedWorkouts} / ${athleteProfile.totalTargetWorkouts}`;

    const completedBar = document.getElementById('completedProgressBar');
    if (completedBar) {
      const pct = Math.round((athleteProfile.completedWorkouts / athleteProfile.totalTargetWorkouts) * 100);
      completedBar.style.width = `${pct}%`;
    }

    // 3. Today's Workout Customization based on push-up level & focus
    renderTodayWorkout();

    // 4. Weekly Schedule List
    renderWeeklySchedule();

    // 5. Recommended Routines Grid
    renderRecommendedRoutines();
  }

  function getWorkoutPresets() {
    const level = athleteProfile.pushupLevel; // Beginner, Intermediate, Advanced
    let pushupReps = '3 Sets × 5 Reps';
    let squatReps = '3 Sets × 10 Reps';
    let plankTime = '3 Sets × 30 Sec';
    let lungeReps = '3 Sets × 8 Reps';
    let restSec = 60;

    if (level === 'Intermediate') {
      pushupReps = '3 Sets × 10 Reps';
      squatReps = '3 Sets × 15 Reps';
      plankTime = '3 Sets × 45 Sec';
      lungeReps = '3 Sets × 12 Reps';
      restSec = 45;
    } else if (level === 'Advanced') {
      pushupReps = '4 Sets × 15+ Reps';
      squatReps = '4 Sets × 20 Reps';
      plankTime = '4 Sets × 60 Sec';
      lungeReps = '4 Sets × 15 Reps';
      restSec = 30;
    }

    return {
      pushupReps,
      squatReps,
      plankTime,
      lungeReps,
      restSec,
      level
    };
  }

  function renderTodayWorkout() {
    const presets = getWorkoutPresets();
    const todayImg = document.getElementById('todayWorkoutImg');
    const todayTitle = document.getElementById('todayWorkoutTitle');
    const todayFocus = document.getElementById('todayWorkoutFocus');
    const todayLevel = document.getElementById('todayWorkoutLevel');
    const todayList = document.getElementById('todayExercisesList');

    if (todayLevel) todayLevel.textContent = presets.level;

    // Primary focus
    const primaryFocus = athleteProfile.focusArea[0] || 'Chest';
    if (todayTitle) todayTitle.textContent = `${primaryFocus} + Power`;
    if (todayFocus) todayFocus.textContent = `Focus: ${athleteProfile.focusArea.join(' • ')} (${athleteProfile.goals[0] || 'Fitness'})`;

    if (todayImg) {
      if (primaryFocus === 'Legs') todayImg.src = 'assets/exercises/squats.png';
      else if (primaryFocus === 'Abs') todayImg.src = 'assets/exercises/plank.png';
      else todayImg.src = 'assets/exercises/pushups.png';
    }

    if (todayList) {
      todayList.innerHTML = `
        <div class="exercise-mini-item">
          <div class="exercise-mini-name">
            <i class="fa-solid fa-circle-play" style="color: #60a5fa;"></i>
            <span>Standard Push-Ups</span>
          </div>
          <span class="exercise-mini-sets">${presets.pushupReps}</span>
        </div>
        <div class="exercise-mini-item">
          <div class="exercise-mini-name">
            <i class="fa-solid fa-circle-play" style="color: #60a5fa;"></i>
            <span>Bodyweight Squats</span>
          </div>
          <span class="exercise-mini-sets">${presets.squatReps}</span>
        </div>
        <div class="exercise-mini-item">
          <div class="exercise-mini-name">
            <i class="fa-solid fa-circle-play" style="color: #60a5fa;"></i>
            <span>Isometric Plank Hold</span>
          </div>
          <span class="exercise-mini-sets">${presets.plankTime}</span>
        </div>
      `;
    }
  }

  function renderWeeklySchedule() {
    const container = document.getElementById('weeklyScheduleContainer');
    const scheduleWeekStatus = document.getElementById('scheduleWeekStatus');
    if (!container) return;

    if (scheduleWeekStatus) {
      scheduleWeekStatus.textContent = `Starting ${athleteProfile.firstDay}`;
    }

    const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const startIdx = daysOfWeek.indexOf(athleteProfile.firstDay);
    const orderedDays = [];
    for (let i = 0; i < 7; i++) {
      orderedDays.push(daysOfWeek[(startIdx + i) % 7]);
    }

    const trainDaysCount = athleteProfile.weeklyTrainingDays;
    // Distribute training days
    let workoutAssignments = [];
    if (trainDaysCount === 1) {
      workoutAssignments = ['Full Body Blast', 'Rest', 'Rest', 'Rest', 'Rest', 'Rest', 'Rest'];
    } else if (trainDaysCount === 2) {
      workoutAssignments = ['Upper Body Push', 'Rest', 'Rest', 'Lower Body Power', 'Rest', 'Rest', 'Rest'];
    } else if (trainDaysCount === 3) {
      workoutAssignments = ['Chest + Arms', 'Rest', 'Legs + Core', 'Rest', 'Full Body Conditioning', 'Rest', 'Rest'];
    } else if (trainDaysCount === 4) {
      workoutAssignments = ['Chest + Triceps', 'Legs + Abs', 'Rest', 'Back + Biceps', 'Full Body Athletic', 'Rest', 'Rest'];
    } else if (trainDaysCount === 5) {
      workoutAssignments = ['Chest Focus', 'Leg Strength', 'Rest', 'Arms + Delts', 'Core & Mobility', 'Metabolic Burn', 'Rest'];
    } else if (trainDaysCount === 6) {
      workoutAssignments = ['Chest & Push', 'Quad & Calves', 'Core Strength', 'Back & Pull', 'Hamstrings & Glutes', 'HIIT Circuit', 'Rest'];
    } else {
      workoutAssignments = ['Chest Push', 'Leg Power', 'Core Isometric', 'Upper Pull', 'Lower Agility', 'Cardio Blast', 'Active Recovery'];
    }

    container.innerHTML = '';
    orderedDays.forEach((day, index) => {
      const routine = workoutAssignments[index];
      const isRest = routine.toLowerCase().includes('rest') || routine.toLowerCase().includes('recovery');
      const isFirstDay = index === 0;

      const row = document.createElement('div');
      row.className = `schedule-day-item ${isFirstDay ? 'today' : ''}`;
      row.innerHTML = `
        <span class="day-badge">${day}</span>
        <span class="workout-target">${routine}</span>
        <span class="workout-status-pill ${isRest ? 'status-rest' : (isFirstDay ? 'status-active' : 'status-done')}">
          ${isRest ? 'REST' : (isFirstDay ? 'SCHEDULED' : 'PLANNED')}
        </span>
      `;
      container.appendChild(row);
    });
  }

  function renderRecommendedRoutines() {
    const grid = document.getElementById('recommendedRoutinesGrid');
    if (!grid) return;

    const presets = getWorkoutPresets();

    grid.innerHTML = `
      <!-- Routine 1: Monday Chest + Arms -->
      <div class="workout-plan-card">
        <div class="workout-plan-banner">
          <img src="assets/exercises/pushups.png" alt="Chest and Arms">
          <span class="badge badge-primary" style="position: absolute; top: 12px; left: 12px;">Day 1 Routine</span>
        </div>
        <div class="workout-plan-body">
          <div>
            <h3 style="font-size: 1.35rem;">Chest + Arms</h3>
            <p style="color: #94a3b8; font-size: 0.88rem;">Push-up progression and upper body volume</p>
          </div>
          <div class="workout-detail-row">
            <span>Push-ups</span>
            <strong style="color: #60a5fa;">${presets.pushupReps}</strong>
          </div>
          <div class="workout-detail-row">
            <span>Rest Interval</span>
            <span>${presets.restSec} sec</span>
          </div>
          <div class="workout-detail-row">
            <span>Intensity</span>
            <span>${presets.level}</span>
          </div>
          <button class="btn btn-secondary" onclick="document.getElementById('todayStartActionBtn').click()">
            <i class="fa-solid fa-play"></i> Start This Routine
          </button>
        </div>
      </div>

      <!-- Routine 2: Wednesday Legs + Core -->
      <div class="workout-plan-card">
        <div class="workout-plan-banner">
          <img src="assets/exercises/squats.png" alt="Legs and Core">
          <span class="badge badge-primary" style="position: absolute; top: 12px; left: 12px;">Day 2 Routine</span>
        </div>
        <div class="workout-plan-body">
          <div>
            <h3 style="font-size: 1.35rem;">Legs + Core</h3>
            <p style="color: #94a3b8; font-size: 0.88rem;">Quad drive, hip stabilizers, and abdominal brace</p>
          </div>
          <div class="workout-detail-row">
            <span>Bodyweight Squats</span>
            <strong style="color: #60a5fa;">${presets.squatReps}</strong>
          </div>
          <div class="workout-detail-row">
            <span>Plank Hold</span>
            <span>${presets.plankTime}</span>
          </div>
          <div class="workout-detail-row">
            <span>Rest Interval</span>
            <span>${presets.restSec} sec</span>
          </div>
          <button class="btn btn-secondary" onclick="document.getElementById('todayStartActionBtn').click()">
            <i class="fa-solid fa-play"></i> Start This Routine
          </button>
        </div>
      </div>

      <!-- Routine 3: Friday Full Body -->
      <div class="workout-plan-card">
        <div class="workout-plan-banner">
          <img src="assets/exercises/lunges.png" alt="Full Body">
          <span class="badge badge-primary" style="position: absolute; top: 12px; left: 12px;">Day 3 Routine</span>
        </div>
        <div class="workout-plan-body">
          <div>
            <h3 style="font-size: 1.35rem;">Full Body Burn</h3>
            <p style="color: #94a3b8; font-size: 0.88rem;">Compound circuit targeting all kinetic chains</p>
          </div>
          <div class="workout-detail-row">
            <span>Walking Lunges</span>
            <strong style="color: #60a5fa;">${presets.lungeReps}</strong>
          </div>
          <div class="workout-detail-row">
            <span>Push-ups + Plank</span>
            <span>3 Super-sets</span>
          </div>
          <div class="workout-detail-row">
            <span>Rest Interval</span>
            <span>${presets.restSec} sec</span>
          </div>
          <button class="btn btn-secondary" onclick="document.getElementById('todayStartActionBtn').click()">
            <i class="fa-solid fa-play"></i> Start This Routine
          </button>
        </div>
      </div>
    `;
  }

  // =========================================================================
  // 8. Live Interactive Workout Player & Timer (Step 19)
  // =========================================================================
  const playerModal = document.getElementById('playerModal');
  const playerCloseBtn = document.getElementById('playerCloseBtn');
  const playerExerciseImg = document.getElementById('playerExerciseImg');
  const playerExerciseIndex = document.getElementById('playerExerciseIndex');
  const playerDifficultyBadge = document.getElementById('playerDifficultyBadge');
  const playerExerciseTitle = document.getElementById('playerExerciseTitle');
  const playerSetsReps = document.getElementById('playerSetsReps');
  const playerTimerDisplay = document.getElementById('playerTimerDisplay');
  const playerTimerMode = document.getElementById('playerTimerMode');
  const playerInstructionsText = document.getElementById('playerInstructionsText');
  const playerToggleTimerBtn = document.getElementById('playerToggleTimerBtn');
  const playerResetTimerBtn = document.getElementById('playerResetTimerBtn');
  const playerNextExerciseBtn = document.getElementById('playerNextExerciseBtn');

  const todayStartActionBtn = document.getElementById('todayStartActionBtn');
  const dashStartWorkoutBtn = document.getElementById('dashStartWorkoutBtn');

  // Exercise Sequence
  const activeWorkoutExercises = [
    {
      title: 'Standard Push-Ups',
      image: 'assets/exercises/pushups.png',
      instructions: 'Keep your body aligned from head to heel and perform each repetition with controlled tempo. Inhale down, exhale press.',
      duration: 60,
      setsReps: '3 Sets × 5-15 Reps'
    },
    {
      title: 'Bodyweight Squats',
      image: 'assets/exercises/squats.png',
      instructions: 'Feet shoulder-width apart. Lower your hips back and down until thighs are parallel with the floor, driving knees out.',
      duration: 60,
      setsReps: '3 Sets × 10-20 Reps'
    },
    {
      title: 'Isometric Plank Hold',
      image: 'assets/exercises/plank.png',
      instructions: 'Rest on elbows and forearms. Contract your glutes, lock your abdominal wall, and prevent any lumbar sagging.',
      duration: 45,
      setsReps: '3 Sets × 30-60 Sec'
    },
    {
      title: 'Walking Lunges',
      image: 'assets/exercises/lunges.png',
      instructions: 'Step forward in an elongated stride, gently kissing the back knee to the floor while keeping your torso tall.',
      duration: 60,
      setsReps: '3 Sets × 12 Reps'
    }
  ];

  let currentExIndex = 0;
  let timerSeconds = 60;
  let isTimerRunning = false;
  let timerInterval = null;

  function openWorkoutPlayer() {
    currentExIndex = 0;
    loadExercise(0);
    playerModal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeWorkoutPlayer() {
    pauseTimer();
    playerModal.classList.remove('active');
    document.body.style.overflow = '';
  }

  function loadExercise(index) {
    if (index >= activeWorkoutExercises.length) {
      // Workout Finished!
      finishWorkoutSession();
      return;
    }

    currentExIndex = index;
    const ex = activeWorkoutExercises[index];

    if (playerExerciseImg) playerExerciseImg.src = ex.image;
    if (playerExerciseIndex) playerExerciseIndex.textContent = `Exercise ${index + 1} of ${activeWorkoutExercises.length}`;
    if (playerDifficultyBadge) playerDifficultyBadge.textContent = athleteProfile.pushupLevel;
    if (playerExerciseTitle) playerExerciseTitle.textContent = ex.title;
    if (playerSetsReps) playerSetsReps.textContent = ex.setsReps;
    if (playerInstructionsText) playerInstructionsText.textContent = ex.instructions;

    pauseTimer();
    timerSeconds = ex.duration;
    updateTimerDisplay();

    if (playerNextExerciseBtn) {
      if (index === activeWorkoutExercises.length - 1) {
        playerNextExerciseBtn.innerHTML = `FINISH WORKOUT <i class="fa-solid fa-flag-checkered"></i>`;
      } else {
        playerNextExerciseBtn.innerHTML = `NEXT EXERCISE <i class="fa-solid fa-forward"></i>`;
      }
    }
  }

  function updateTimerDisplay() {
    const mins = Math.floor(timerSeconds / 60);
    const secs = timerSeconds % 60;
    if (playerTimerDisplay) {
      playerTimerDisplay.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
  }

  function startTimer() {
    if (isTimerRunning) return;
    isTimerRunning = true;
    AudioEngine.playBeep();

    if (playerToggleTimerBtn) {
      playerToggleTimerBtn.innerHTML = `<i class="fa-solid fa-pause"></i> PAUSE`;
    }
    if (playerTimerMode) playerTimerMode.textContent = 'ACTIVE SET';

    timerInterval = setInterval(() => {
      if (timerSeconds > 0) {
        timerSeconds--;
        updateTimerDisplay();
        if (timerSeconds === 3 || timerSeconds === 2 || timerSeconds === 1) {
          AudioEngine.playTone(800, 'sine', 0.08);
        }
      } else {
        pauseTimer();
        AudioEngine.playSuccess();
        if (playerTimerMode) playerTimerMode.textContent = 'REST INTERVAL COMPLETE';
        showToast('Set finished! Take a quick sip of water.', 'success');
      }
    }, 1000);
  }

  function pauseTimer() {
    isTimerRunning = false;
    clearInterval(timerInterval);
    if (playerToggleTimerBtn) {
      playerToggleTimerBtn.innerHTML = `<i class="fa-solid fa-play"></i> START`;
    }
  }

  function resetTimer() {
    pauseTimer();
    const ex = activeWorkoutExercises[currentExIndex];
    timerSeconds = ex ? ex.duration : 60;
    updateTimerDisplay();
  }

  function finishWorkoutSession() {
    closeWorkoutPlayer();
    AudioEngine.playSuccess();

    // Increment completed workouts and streak
    athleteProfile.completedWorkouts = Math.min(athleteProfile.totalTargetWorkouts, athleteProfile.completedWorkouts + 1);
    athleteProfile.streak += 1;
    saveProfile();
    renderDashboard();

    showToast('Workout Completed! Superb dedication!', 'success');

    // Open Feedback Modal
    setTimeout(() => {
      openFeedbackModal();
    }, 600);
  }

  if (todayStartActionBtn) todayStartActionBtn.addEventListener('click', openWorkoutPlayer);
  if (dashStartWorkoutBtn) dashStartWorkoutBtn.addEventListener('click', openWorkoutPlayer);
  if (playerCloseBtn) playerCloseBtn.addEventListener('click', closeWorkoutPlayer);

  if (playerToggleTimerBtn) {
    playerToggleTimerBtn.addEventListener('click', () => {
      if (isTimerRunning) pauseTimer();
      else startTimer();
    });
  }

  if (playerResetTimerBtn) playerResetTimerBtn.addEventListener('click', resetTimer);

  if (playerNextExerciseBtn) {
    playerNextExerciseBtn.addEventListener('click', () => {
      AudioEngine.playBeep();
      loadExercise(currentExIndex + 1);
    });
  }

  // =========================================================================
  // 9. Feedback Modal & Submission Logic (Step 20)
  // =========================================================================
  const feedbackModal = document.getElementById('feedbackModal');
  const feedbackCloseBtn = document.getElementById('feedbackCloseBtn');
  const dashFeedbackBtn = document.getElementById('dashFeedbackBtn');
  const starRatingRow = document.getElementById('starRatingRow');
  const suitYesBtn = document.getElementById('suitYesBtn');
  const suitNoBtn = document.getElementById('suitNoBtn');
  const submitFeedbackBtn = document.getElementById('submitFeedbackBtn');
  const feedbackFormView = document.getElementById('feedbackFormView');
  const feedbackSuccessBox = document.getElementById('feedbackSuccessBox');
  const feedbackDoneBtn = document.getElementById('feedbackDoneBtn');

  let selectedRating = 5;
  let isSuitable = true;

  function openFeedbackModal() {
    if (feedbackFormView) feedbackFormView.style.display = 'block';
    if (feedbackSuccessBox) feedbackSuccessBox.classList.remove('active');
    feedbackModal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeFeedbackModal() {
    feedbackModal.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (dashFeedbackBtn) dashFeedbackBtn.addEventListener('click', openFeedbackModal);
  if (feedbackCloseBtn) feedbackCloseBtn.addEventListener('click', closeFeedbackModal);

  // Star Rating Interaction
  if (starRatingRow) {
    const stars = starRatingRow.querySelectorAll('.star-icon');
    stars.forEach(star => {
      star.addEventListener('click', () => {
        AudioEngine.playBeep();
        const rating = parseInt(star.getAttribute('data-rating'), 10);
        selectedRating = rating;
        stars.forEach(s => {
          const r = parseInt(s.getAttribute('data-rating'), 10);
          s.classList.toggle('active', r <= rating);
        });
      });
    });
  }

  // Suitability Buttons
  if (suitYesBtn && suitNoBtn) {
    suitYesBtn.addEventListener('click', () => {
      isSuitable = true;
      suitYesBtn.classList.add('active');
      suitNoBtn.classList.remove('active');
    });
    suitNoBtn.addEventListener('click', () => {
      isSuitable = false;
      suitNoBtn.classList.add('active');
      suitYesBtn.classList.remove('active');
    });
  }

  // Submit Feedback
  if (submitFeedbackBtn) {
    submitFeedbackBtn.addEventListener('click', () => {
      const commentInput = document.getElementById('feedbackCommentInput');
      const comment = commentInput ? commentInput.value.trim() : '';

      athleteProfile.feedbackGiven = true;
      saveProfile();

      AudioEngine.playSuccess();
      if (feedbackFormView) feedbackFormView.style.display = 'none';
      if (feedbackSuccessBox) feedbackSuccessBox.classList.add('active');
    });
  }

  if (feedbackDoneBtn) {
    feedbackDoneBtn.addEventListener('click', () => {
      closeFeedbackModal();
      activateDashboardView();
    });
  }

  // =========================================================================
  // 10. Profile Reset & Utility Controls (Step 21 & 23)
  // =========================================================================
  const dashResetProfileBtn = document.getElementById('dashResetProfileBtn');
  if (dashResetProfileBtn) {
    dashResetProfileBtn.addEventListener('click', () => {
      if (confirm('Are you sure you want to reset your profile and stored workout metrics?')) {
        localStorage.removeItem(STORAGE_KEY);
        athleteProfile = { ...defaultProfile };
        saveProfile();
        renderDashboard();
        showToast('Profile reset to default state.', 'success');
        location.reload();
      }
    });
  }

  const toggleAllDaysBtn = document.getElementById('toggleAllDaysBtn');
  if (toggleAllDaysBtn) {
    toggleAllDaysBtn.addEventListener('click', () => {
      const grid = document.getElementById('recommendedRoutinesGrid');
      if (grid) {
        grid.scrollIntoView({ behavior: 'smooth' });
        showToast('Viewing full weekly routine sequence');
      }
    });
  }

  // Footer Program Links
  ['FullBody', 'Hypertrophy', 'Legs', 'WeightLoss'].forEach(type => {
    const el = document.getElementById(`footerLink${type}`);
    if (el) {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        openAssessment();
      });
    }
  });

  // Initial load check: if user already has saved data in localStorage, render dashboard
  renderDashboard();
  const savedData = localStorage.getItem(STORAGE_KEY);
  if (savedData) {
    // Show "My Plan" in navbar
    if (navDashboardLink) navDashboardLink.style.display = 'inline-block';
    if (mobileDashboardLink) mobileDashboardLink.style.display = 'block';
  }
});
