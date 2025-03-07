document.addEventListener('DOMContentLoaded', function() {
    // 광고 초기 로드
    function initializeAds() {
        try {
            (adsbygoogle = window.adsbygoogle || []).push({});
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
        fetch('check_ip.php')
            .then(response => response.json())
            .then(data => {
                if (!data.hasVisited) {
                    const adPopup = document.getElementById('adPopup');
                    const overlay = document.getElementById('overlay');
                    if (adPopup && overlay) {
                        adPopup.style.display = 'block';
                        overlay.style.display = 'block';
                        disableScroll();
                        startTimer();
                    }
                }
            })
            .catch(error => console.error('IP 체크 오류:', error));
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
    initializeAds();  // 광고 초기화
    showAdPopup();    // 팝업 표시
});
