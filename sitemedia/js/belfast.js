$("document").ready(function(){

  $("a.toggle-section").on('click',function(evt){
    evt.preventDefault();
    var $this = $(this),
        $collaspeSection = $(".collaspe-section");

      $collaspeSection.toggleClass('collasped');
      $(this).toggleClass('collasped');

      if($collaspeSection.hasClass('collasped')){
        $collaspeSection.slideUp();
      }
      else{
        $collaspeSection.slideDown();
      }

  });

  $(".nav-list.sidenav").affix({
     offset: {
      top: 0,
      bottom: function () {
        return (this.bottom = $('.footer').outerHeight(true))
      }
    }
  });

  function checkWindowHeight(){
    var $window = $(window),
        $sidenav = $('.nav-list.sidenav');

        console.log($window.height())
        console.log($sidenav.height()+100)
    if($window.height() < $sidenav.height()+$sidenav.offset().top){
      $sidenav.addClass('relative');
    }
    else{
      $sidenav.removeClass('relative');
    }
  }

  checkWindowHeight();

  $(window).resize(function(){
    checkWindowHeight();
  });

});//end doc.ready