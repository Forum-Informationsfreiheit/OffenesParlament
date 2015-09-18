$ = require 'jquery'

# This makes sure the homepage fills the viewport and the footer is at the bottom
# edge when the viewport is larger than the content

padding = 0

expand_search_container_to_viewport = () ->
  console.log 'resize'
  body_height = $('body').height()
  viewport_height = $(window).height()
  content_box = $('.homepage_content')
  padding = Math.ceil( (viewport_height-body_height+2*padding)/2 )
  if padding < 0 then padding = 0
  content_box.css(
    paddingTop: padding
    paddingBottom: padding
  )

$(document).ready(expand_search_container_to_viewport)
$(window).resize(expand_search_container_to_viewport)
