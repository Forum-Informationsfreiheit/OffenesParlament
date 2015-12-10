AppDispatcher = require('../dispatcher/AppDispatcher.coffee')
AnysearchConstants = require('../constants/AnysearchConstants.coffee')


LLP_URL_REGEXP = /^(.+)(\/)([XIVMDC]{1,})(\/)?$/


RouterActions =
  changeLlpUrl: (llp) ->
    #redirect the user to the new LLP they just set via the Anysearch-bar
    url_matches = LLP_URL_REGEXP.exec(location.href)
    if url_matches and url_matches.length > 3
      url_matches[3] = llp
      url_matches.shift()
      location.href = url_matches.join('')


module.exports = RouterActions
