$("document").ready(function(){


  var $poets = $("#poets");
  if($poets.length>0){
   $poets.masonry({
      "itemSelector": 'figure',
      "columnWidth": 1
    });
  }

  var $bios = $("#bios");
  if($bios.length>0){
   $bios.masonry({
      "itemSelector": '.panel',
      "columnWidth": 40,
      "gutter": 10
    })
  }

  $("a.toggle-section").on('click',function(evt){
    evt.preventDefault();
    var $this = $(this),
        $collaspeSection = $(".collaspe-section");

      $collaspeSection.toggleClass('collasped');
      $(this).toggleClass('collasped active');

      if($collaspeSection.hasClass('collasped')){
        $collaspeSection.slideUp();
      }
      else{
        $collaspeSection.slideDown();
      }

  });

  var $sidenav = $(".nav-list.sidenav");

  if($sidenav.length>0){
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
          $sidenav = $('.sidenav'),
          offset = $sidenav.offset();

      if($window.height() < $sidenav.height()+offset.top){
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
  }

});//end doc.ready