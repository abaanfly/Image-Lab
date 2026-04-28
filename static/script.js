/**
 * Image Manipulation Lab — Frontend Logic
 * Abaan Ali · CS-1102 · Ashoka University
 */

// ── DOM REFERENCES ──────────────────────────────────────────────────────────
const uploadZone        = document.getElementById("uploadZone");
const fileInput         = document.getElementById("fileInput");
const workspace         = document.getElementById("workspace");
const effectBtns        = document.querySelectorAll(".effect-btn");
const loader            = document.getElementById("loader");
const viewerPlaceholder = document.getElementById("viewerPlaceholder");
const viewer            = document.getElementById("viewer");
const originalImg       = document.getElementById("originalImg");
const resultImg         = document.getElementById("resultImg");
const compareWrapper    = document.getElementById("compareWrapper");
const beforeClip        = document.getElementById("beforeClip");
const compareHandle     = document.getElementById("compareHandle");
const activeEffectLbl   = document.getElementById("activeEffectLabel");
const downloadBtn       = document.getElementById("downloadBtn");
const resetBtn          = document.getElementById("resetBtn");
const panelRight        = document.getElementById("panelRight");

// ── STATE ────────────────────────────────────────────────────────────────────
let originalBase64 = null;
let resultBase64   = null;
let currentEffect  = null;

// ── UPLOAD HANDLING ──────────────────────────────────────────────────────────
uploadZone.addEventListener("click", () => fileInput.click());

uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("drag-over");
});
uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("drag-over");
});
uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) loadImage(file);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) loadImage(fileInput.files[0]);
});

function loadImage(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    originalBase64 = e.target.result;

    // Switch from upload zone to side-by-side workspace
    uploadZone.style.display = "none";
    workspace.style.display  = "grid";

    // Right panel shows placeholder until an effect is chosen
    showRightPanel("placeholder");

    effectBtns.forEach(b => b.classList.remove("active"));
    currentEffect = null;
  };
  reader.readAsDataURL(file);
}

// ── RIGHT PANEL STATE SWITCHER ───────────────────────────────────────────────
function showRightPanel(state) {
  viewerPlaceholder.style.display = state === "placeholder" ? "flex"   : "none";
  loader.style.display            = state === "loading"     ? "flex"   : "none";
  viewer.style.display            = state === "viewer"      ? "flex"   : "none";
}

// ── EFFECT BUTTONS ──────────────────────────────────────────────────────────
effectBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    if (!originalBase64) return;
    effectBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentEffect = btn.dataset.effect;
    sendToBackend(currentEffect);
  });
});

async function sendToBackend(effect) {
  showRightPanel("loading");

  try {
    const response = await fetch("/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: originalBase64, effect })
    });

    const data = await response.json();

    if (data.error) {
      alert("Error: " + data.error);
      showRightPanel("placeholder");
      return;
    }

    resultBase64 = data.result;
    showViewer(effect, data.result);

  } catch (err) {
    alert("Could not connect to server. Is Flask running?");
    console.error(err);
    showRightPanel("placeholder");
  }
}

// ── VIEWER ───────────────────────────────────────────────────────────────────
function showViewer(effect, resultDataUrl) {
  // Set image sources BEFORE showing
  resultImg.src   = resultDataUrl;
  originalImg.src = originalBase64;

  activeEffectLbl.textContent = effect.replace("_", " ");
  showRightPanel("viewer");

  // Wait for the result image to load so we know its rendered size,
  // then size the before-image to match exactly — this is the slider fix.
  resultImg.onload = syncImages;

  // If already cached / instant load
  if (resultImg.complete && resultImg.naturalWidth > 0) {
    syncImages();
  }

  setSliderPosition(50);
}

/**
 * THE SLIDER FIX:
 * The before-image must be the same pixel width as the compare-wrapper
 * so both images render at the identical size and line up perfectly.
 * We set an explicit px width on the before-image that matches the wrapper.
 */
function syncImages() {
  const w = compareWrapper.offsetWidth;
  originalImg.style.width = w + "px";
}

window.addEventListener("resize", () => {
  if (viewer.style.display !== "none") syncImages();
});

function setSliderPosition(pct) {
  const clamped = Math.min(100, Math.max(0, pct));
  beforeClip.style.width   = clamped + "%";
  compareHandle.style.left = clamped + "%";
}

// ── DRAG SLIDER ──────────────────────────────────────────────────────────────
let isDragging = false;

compareWrapper.addEventListener("mousedown",  startDrag);
compareWrapper.addEventListener("touchstart", startDrag, { passive: true });
window.addEventListener("mousemove",  onDrag);
window.addEventListener("touchmove",  onDrag, { passive: true });
window.addEventListener("mouseup",   stopDrag);
window.addEventListener("touchend",  stopDrag);

function startDrag(e) {
  isDragging = true;
  updateSlider(e);
}
function onDrag(e) {
  if (!isDragging) return;
  updateSlider(e);
}
function stopDrag() { isDragging = false; }

function updateSlider(e) {
  const rect    = compareWrapper.getBoundingClientRect();
  const clientX = e.touches ? e.touches[0].clientX : e.clientX;
  const pct     = ((clientX - rect.left) / rect.width) * 100;
  setSliderPosition(pct);
}

// ── DOWNLOAD ─────────────────────────────────────────────────────────────────
downloadBtn.addEventListener("click", () => {
  if (!resultBase64) return;
  const a    = document.createElement("a");
  a.href     = resultBase64;
  a.download = `imglab_${currentEffect || "result"}.png`;
  a.click();
});

// ── RESET ────────────────────────────────────────────────────────────────────
resetBtn.addEventListener("click", () => {
  originalBase64 = null;
  resultBase64   = null;
  currentEffect  = null;
  fileInput.value = "";

  workspace.style.display  = "none";
  uploadZone.style.display = "block";

  effectBtns.forEach(b => b.classList.remove("active"));
});