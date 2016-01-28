jQuery = require 'jquery'

getCookie = (name) ->
    cookieValue = null
    if(document.cookie && document.cookie != '')
        cookies = document.cookie.split(';')
        for cookie in cookies
            cookie = jQuery.trim(cookie)
            # Does this cookie string begin with the name we want?
            if(cookie.substring(0, name.length + 1) == (name + '='))
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break
    return cookieValue


module.exports =
  get_csrf_token: () ->
    return getCookie('csrftoken')
