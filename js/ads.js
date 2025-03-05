document.addEventListener('DOMContentLoaded', function() {
    // 광고 초기 로드
    function initializeAds() {
        try {
            const ads = document.querySelectorAll('.adsbygoogle');
            ads.forEach(ad => {
                (adsbygoogle = window.adsbygoogle || []).push({});
            });
        } catch (e) {
            console.error('광고 초기화 실패:', e);
        }
    }

    // 스크롤 제어
    function disableScroll() {
        document.body.style.overflow = 'hidden';
    }
    
    function enableScroll() {
        document.body.style.overflow = 'auto';
    }

    // 광고 팝업 표시
    function showAdPopup() {
        const adPopup = document.getElementById('adPopup');
        const overlay = document.getElementById('overlay');
        const popupAdContainer = document.getElementById('popupAdContainer');
        const preloadedAd = document.querySelector('.popup-ad');

        if (adPopup && overlay && preloadedAd && popupAdContainer) {
            popupAdContainer.appendChild(preloadedAd);
            adPopup.style.display = 'block';
            overlay.style.display = 'block';
            startTimer();
        }
    }

    // 타이머 기능
    function startTimer() {
        let timeLeft = 7;
        const timerElement = document.getElementById('timer');
        const closeBtn = document.getElementById('closeBtn');
        
        const timer = setInterval(function() {
            timeLeft--;
            if (timerElement) timerElement.textContent = timeLeft;
            
            if (timeLeft <= 0) {
                clearInterval(timer);
                if (closeBtn) {
                    closeBtn.disabled = false;
                    closeBtn.addEventListener('click', function() {
                        document.getElementById('adPopup').style.display = 'none';
                        document.getElementById('overlay').style.display = 'none';
                        enableScroll();
                    });
                }
                if (timerElement) timerElement.style.display = 'none';
            }
        }, 1000);
    }

    // 초기화
    disableScroll();
    initializeAds();
    showAdPopup();
});
