React = require 'react'
ReactDOM = require 'react-dom'
SearchResults = require './components/SearchResults.cjsx'
SubscriptionModal = require './components/SubscriptionModal.cjsx'
SubscriptionModalStore = require './stores/SubscriptionModalStore.coffee'
SubscriptionModalActions = require './actions/SubscriptionModalActions.coffee'
AnysearchStore = require './stores/AnysearchStore.coffee'
AnysearchActions = require './actions/AnysearchActions.coffee'
$ = require 'jquery'
_ = require 'underscore'
require './utils/csrf_token.coffee'
tooltip = require 'tooltip'
app_router = require('./utils/router.coffee')


$(document).ready( () ->
  #init tooltips
  tooltip({
    showDelay: 10
    offset: {x: 0, y: 0}
    style:
      borderColor: 'white'
  })

  # make menu responsive
  menu = $('.menu_bar ul.main_menu')
  toggle = $('.menu_bar .menu_responsive_sandwich')
  toggle.on('click', (event) ->
    event.preventDefault()
    menu.slideToggle()
  )

  # try to get all containers for react components on the page
  anysearch_container = document.getElementById('anysearch_container')
  anysearch_container_homepage = document.getElementById('anysearch_container_homepage')
  content_container = document.getElementById('content')
  modal_container = document.getElementById('react_modal_container')

  # when page has an anysearch_container (every page except homepage) render anysearch bar
  if anysearch_container
    Searchbar = require("./components/anysearch/Searchbar.cjsx")
    AnysearchActions.createPermanentTerm('llps', OFFPARL_DATA_GGP)
    if OFFPARL_DATA_SEARCH_TYPE?
      AnysearchActions.createTerm('type', OFFPARL_DATA_SEARCH_TYPE)
    AnysearchActions.declareSearchbarSetupComplete()
    ReactDOM.render(
      React.createElement(Searchbar, {}),
      anysearch_container
    )
  # we're on the homepage -> render special anysearch for homepage
  else if anysearch_container_homepage
    Searchbar = require("./components/anysearch/Searchbar.cjsx")
    AnysearchActions.createTerm('llps', OFFPARL_DATA_GGP)
    AnysearchActions.declareSearchbarSetupComplete()
    ReactDOM.render(
      React.createElement(Searchbar, {}),
      anysearch_container_homepage
    )

  # render search results if store has results
  render_results = () ->
    results = AnysearchStore.get_search_results()
    if content_container and results
      SearchResults = require("./components/SearchResults.cjsx")
      ReactDOM.render(
        React.createElement(SearchResults, {results: results}),
        content_container
      )
  AnysearchStore.addChangeListener(render_results)
  render_results()

  app_router.start()

  # modal component to display subscription-modals
  render_modal = () ->
    if modal_container
      data =
        show: SubscriptionModalStore.is_modal_shown()
        subscription_url: SubscriptionModalStore.get_subscription_url()
        subscription_title: SubscriptionModalStore.get_subscription_title()
        server_status: SubscriptionModalStore.get_server_status()
        email: SubscriptionModalStore.get_email()
      ReactDOM.render(
        React.createElement(SubscriptionModal, data),
        modal_container
      )
  SubscriptionModalStore.addChangeListener(render_modal)
  render_modal()

  #activate generic HTML links that should open a subscription modal
  $('.subscription_button').click((e) ->
    e.preventDefault()
    btn = $(e.target)
    url = btn.data('subscription_url')
    title = btn.data('subscription_title')
    SubscriptionModalActions.showModal(url, title)
  )
)
