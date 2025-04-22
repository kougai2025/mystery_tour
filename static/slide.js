const swiper = new Swiper(".swiper", {
    slidesPerView: 1.1,
    spaceBetween: 2, //スライド同士の余白
    centeredSlides: true, //スライドを真ん中に配置させる
    loop: false,
    
    navigation: {
      nextEl: ".swiper-button-next",
      prevEl: ".swiper-button-prev"
    }
  });