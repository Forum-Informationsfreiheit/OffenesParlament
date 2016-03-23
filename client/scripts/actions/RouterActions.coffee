app_router = require('../utils/router.coffee')


LLP_URL_REGEXP = /^(.+)(\/)([XIVMDC]{1,})(\/)?$/


RouterActions =
  changeLlpUrl: (llp) ->
    #redirect the user to the new LLP they just set via the Anysearch-bar
    url_matches = LLP_URL_REGEXP.exec(location.href)
    if url_matches and url_matches.length > 3
      url_matches[3] = llp
      url_matches.shift()
      location.href = url_matches.join('')

  changeLocation: (route) ->
    location.href = route

  changeRoute: (route) ->
    app_router.navigate(route)


module.exports = RouterActions
