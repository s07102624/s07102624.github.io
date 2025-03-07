document.addEventListener('DOMContentLoaded', function() {
    // 광고 초기화 순서 변경
    function initializeAds() {
        try {
            // 상단 광고를 먼저 초기화
            const topAd = document.querySelector('.top-ad .adsbygoogle');
            if (topAd && !topAd.hasAttribute('data-adsbygoogle-initialized')) {
                (adsbygoogle = window.adsbygoogle || []).push({});
                topAd.setAttribute('data-adsbygoogle-initialized', 'true');
            }

            // 나머지 광고들 초기화
            document.querySelectorAll('.adsbygoogle:not([data-adsbygoogle-initialized])').forEach(function(ad) {
                (adsbygoogle = window.adsbygoogle || []).push({});
                ad.setAttribute('data-adsbygoogle-initialized', 'true');
            });
        } catch (e) {
            console.error('광고 초기화 실패:', e);
        }
    }

    // 스크롤 제어 함수들
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
            // 미리 로드된 광고를 팝업으로 이동
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
    initializeAds();  // 모든 광고 초기화
    showAdPopup();    // 팝업 광고 표시
});
