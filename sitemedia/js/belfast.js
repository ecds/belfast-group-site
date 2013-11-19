$("document").ready(function(){
  $("#poets").masonry({
    "itemSelector": 'figure',
    "columnWidth": 1
  })

  .on('mouseover','figure',function(){
    $(this).siblings("figure").children('img').stop().animate({"opacity":0.5});
  })
  .on('mouseout','figure',function(){
    $(this).siblings("figure").children('img').stop().animate({"opacity":1});
  })
  .on('click','figure',function(){
    $url = $(this).find('a').attr('href');
    window.location.assign($url);
  });

});