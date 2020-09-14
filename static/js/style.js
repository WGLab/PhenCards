
$(document).ready(function(){
  // Add smooth scrolling to all links
  $("a").on('click', function(event) {

    // Make sure this.hash has a value before overriding default behavior
    if (this.hash !== "") {
      // Prevent default anchor click behavior
      event.preventDefault();

      // Store hash
      var hash = this.hash;

      // Using jQuery's animate() method to add smooth page scroll
      // The optional number (800) specifies the number of milliseconds it takes to scroll to the specified area
      $('html, body').animate({
        scrollTop: $(hash).offset().top - 100
      }, 800);
    }
  });
});

$(document).ready(function(){
 $('li a').click(function(){
   $('li a').removeClass('active');
   $(this).addClass('active');
 });
});

$(window).on('scroll', function() {
    $('.container.medium').each(function() {
        if($(window).scrollTop() >= $(this).offset().top - $("#navbarcon").height()){
            var id = $(this).attr('id');
            $('li a').removeClass('active');
            $('li a[href="#'+ id +'"]').addClass('active');
        }
    });
});

//for mobile
if (/Mobi|Android/i.test(navigator.userAgent)) {
         $(".nav-item").css('font-size', '1.8em');
         $(".navbar").css('height', '120px');
}

$(window).resize(function(){
    width = $(window).width();
    $('.table').each(function() {
        $(this)
    }); 
    });
