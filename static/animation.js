// 경로: static/animation.js
// 입자 애니메이션 & 색 공 생성 로직

// 색 선택 후 입자 효과 → 공 형성 → 캘린더 이동
function createParticleEffect(colorValue, colorSolid) {
  // 입자 컨테이너 생성
  const particleContainer = document.createElement('div');
  particleContainer.className = 'particle-container';
  document.body.appendChild(particleContainer);

  // 선택된 컬러칩 위치 가져오기
  const selectedChip = document.querySelector('.color-chip input[type="radio"]:checked').closest('.color-chip');
  const chipRect = selectedChip.getBoundingClientRect();
  const centerX = chipRect.left + chipRect.width / 2;
  const centerY = chipRect.top + chipRect.height / 2;

  // 30개의 입자 생성
  const particles = [];
  for (let i = 0; i < 30; i++) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.background = colorSolid;
    particle.style.left = centerX + 'px';
    particle.style.top = centerY + 'px';
    particle.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
    particleContainer.appendChild(particle);
    particles.push(particle);

    // 랜덤 방향으로 퍼짐 (더 빠르게)
    const angle = (Math.PI * 2 * i) / 30;
    const distance = 120 + Math.random() * 40;
    const targetX = Math.cos(angle) * distance;
    const targetY = Math.sin(angle) * distance;

    setTimeout(() => {
      particle.style.transform = `translate(${targetX}px, ${targetY}px) scale(0.6)`;
      particle.style.opacity = '0.9';
    }, 30);
  }

  // 0.6초 후: 입자들이 모여서 공 형성 (더 빠르게)
  setTimeout(() => {
    particles.forEach(particle => {
      particle.style.transition = 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
      particle.style.transform = 'translate(0, 0) scale(1)';
      particle.style.opacity = '1';
    });
  }, 600);

  // 1.1초 후: 하나의 공으로 합쳐짐 (더 빠르게)
  setTimeout(() => {
    particles.forEach((particle, index) => {
      if (index > 0) {
        particle.style.transition = 'all 0.3s ease-out';
        particle.style.opacity = '0';
        particle.style.transform = 'scale(0)';
      }
    });

    // 첫 번째 입자를 공으로 변환
    const orb = particles[0];
    orb.className = 'color-orb';
    orb.style.transition = 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
    orb.style.width = '60px';
    orb.style.height = '60px';
    orb.style.borderRadius = '50%';
    orb.style.boxShadow = `0 8px 32px rgba(0, 0, 0, 0.3), inset 0 2px 8px rgba(255, 255, 255, 0.3)`;
    orb.style.transform = 'scale(1.2)';
    orb.style.opacity = '1';

    // 공 살짝 튕기는 효과
    setTimeout(() => {
      orb.style.transform = 'scale(1)';
    }, 100);

  }, 1100);

  // 1.5초 후: 미니 캘린더 표시 & 공이 날아감 (더 빠르게)
  setTimeout(() => {
    showMiniCalendar(colorSolid, particles[0], centerX, centerY);
  }, 1500);
}

// 미니 캘린더 표시 & 공 박기
function showMiniCalendar(colorSolid, orb, startX, startY) {
  // 미니 캘린더 생성
  const calendar = document.createElement('div');
  calendar.className = 'mini-calendar';
  calendar.innerHTML = `
    <div class="calendar-header">
      ${new Date().getFullYear()}년 ${new Date().getMonth() + 1}월
    </div>
    <div class="calendar-grid">
      ${generateCalendarDays()}
    </div>
  `;
  document.body.appendChild(calendar);

  // 캘린더 페이드 인 (더 빠르게)
  setTimeout(() => {
    calendar.style.opacity = '1';
    calendar.style.transform = 'translateY(0) scale(1)';
  }, 50);

  // 오늘 날짜 찾기
  const today = new Date().getDate();
  const todayCell = calendar.querySelector(`.day-cell[data-day="${today}"]`);

  if (todayCell) {
    const todayRect = todayCell.getBoundingClientRect();

    // 공이 날짜 칸으로 이동 (더 빠르게)
    setTimeout(() => {
      const targetX = todayRect.left + todayRect.width / 2 - startX;
      const targetY = todayRect.top + todayRect.height / 2 - startY;

      // 포물선 궤적을 위한 keyframe 애니메이션
      orb.style.transition = 'all 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
      orb.style.transform = `translate(${targetX}px, ${targetY}px) scale(0.6)`;

      // 날짜 칸에 도착하면 반짝임 효과
      setTimeout(() => {
        // 공 흡수 효과
        orb.style.transition = 'all 0.3s ease-out';
        orb.style.transform = `translate(${targetX}px, ${targetY}px) scale(0)`;
        orb.style.opacity = '0';

        // 날짜 칸 색깔 변경 + 펄스 효과
        todayCell.style.transition = 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
        todayCell.style.background = colorSolid;
        todayCell.style.transform = 'scale(1.15)';
        todayCell.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.25)';

        setTimeout(() => {
          todayCell.style.transform = 'scale(1)';
        }, 200);

        // 입자 컨테이너 제거
        setTimeout(() => {
          document.querySelector('.particle-container')?.remove();
          
          // 페이드 아웃 후 다음 단계로 (더 빠르게)
          setTimeout(() => {
            calendar.style.transition = 'all 0.4s ease-out';
            calendar.style.opacity = '0';
            calendar.style.transform = 'translateY(-20px) scale(0.95)';
            setTimeout(() => {
              calendar.remove();
              // Step 2로 이동
              document.querySelector('form').submit();
            }, 400);
          }, 600);
        }, 200);
      }, 700);
    }, 200);
  }
}

// 캘린더 날짜 생성
function generateCalendarDays() {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const todayDate = today.getDate();

  let html = '';

  // 요일 헤더
  const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
  dayNames.forEach(day => {
    html += `<div class="day-name">${day}</div>`;
  });

  // 빈 칸
  for (let i = 0; i < firstDay; i++) {
    html += '<div class="day-cell empty"></div>';
  }

  // 날짜
  for (let day = 1; day <= daysInMonth; day++) {
    const isToday = day === todayDate;
    html += `<div class="day-cell ${isToday ? 'today' : ''}" data-day="${day}">${day}</div>`;
  }

  return html;
}

// 페이지 로드 시 폼 제출 인터셉트
document.addEventListener('DOMContentLoaded', () => {
  const colorForm = document.querySelector('form');
  if (colorForm && document.querySelector('.color-grid')) {
    colorForm.addEventListener('submit', (e) => {
      const selectedInput = document.querySelector('.color-chip input[type="radio"]:checked');
      if (selectedInput) {
        e.preventDefault();
        
        // 선택된 색상 정보 가져오기
        const colorValue = selectedInput.value;
        const chipVisual = selectedInput.closest('.color-chip').querySelector('.chip-visual');
        const colorSolid = chipVisual.style.background;

        // 입자 애니메이션 시작
        createParticleEffect(colorValue, colorSolid);
      }
    });
  }
});
