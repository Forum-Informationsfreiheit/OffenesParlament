AnysearchActions = require('../actions/AnysearchActions.coffee')
Backbone = require('backbone')


AppRouter = Backbone.Router.extend({
    routes: {
        "suche/(:type)(/)": "searchRoute"
    }
})

app_router = new AppRouter

app_router.on('route:searchRoute', (endpoint, query) ->
  AnysearchActions.overrideSearch(endpoint, query)
)


module.exports =
  navigate: (route) ->
    app_router.navigate(route, {trigger: false, replace: false})
  start: () ->
    Backbone.history.start({pushState: true})


