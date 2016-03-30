React = require 'react'
ReactDOM = require 'react-dom'
SearchResults = require './components/results/SearchResults.cjsx'
ResultsPreview = require './components/anysearch/ResultsPreview.cjsx'
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

  # limited tables
  tables = $('.limited_table')
  $.each(tables, (key, t) ->
    table = $(t)
    rows = table.find('tbody tr')
    visible_items = table.data('limited_table_visible_items') or 10
    if visible_items < rows.length
      $.each(rows, (key, r) ->
        if key >= visible_items
          $(r).addClass('limited_table_hidden_row')
      )
      show_all_link = $('<a href="#" class="limited_table_show_all_link icon_link icon_arrow_down">Alle ' + rows.length + ' Einträge anzeigen</a>')
      show_all_link.click((e) ->
        e.preventDefault()
        hidden_rows = table.find('tbody tr.limited_table_hidden_row')
        $.each(hidden_rows, (key, r) ->
          $(r).removeClass('limited_table_hidden_row')
        )
        show_all_link.remove()
      )
      table.after(show_all_link)
  )

  # try to get all containers for react components on the page
  anysearch_container = document.getElementById('anysearch_container')
  anysearch_container_homepage = document.getElementById('anysearch_container_homepage')
  anysearch_container_homepage_help = document.getElementById('anysearch_container_homepage_help')
  content_container = document.getElementById('content')
  modal_container = document.getElementById('react_modal_container')

  # when page has an anysearch_container (every page except homepage) render anysearch bar
  if anysearch_container
    Searchbar = require("./components/anysearch/Searchbar.cjsx")
    AnysearchActions.createPermanentTerm('llps', OFFPARL_DATA_GGP)
    if OFFPARL_DATA_SEARCH_TYPE?
      AnysearchActions.createTerm('type', OFFPARL_DATA_SEARCH_TYPE)
    AnysearchActions.declareSearchbarSetupComplete()
    AnysearchActions.activateSearchbarRouting()
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
    ReactDOM.render(
      React.createElement(ResultsPreview, {}),
      anysearch_container_homepage_help
    )
    $('.anysearch_submit_button').click((e) ->
      e.preventDefault()
      AnysearchActions.forceLocationChange()
    )

  # render search results if store has results
  render_results = () ->
    results = AnysearchStore.get_search_results()
    if content_container and results
      document.title = AnysearchStore.get_subscription_title() + " - OffenesParlament.at"
      $('.law_vorparlamentarisch_background').remove()
      ReactDOM.render(
        React.createElement(SearchResults, {
          results: results
          allow_subscription: AnysearchStore.is_subscription_allowed()
          subscription_url: AnysearchStore.get_subscription_url()
          search_ui_url: AnysearchStore.get_search_ui_url()
          subscription_title: AnysearchStore.get_subscription_title()
        }),
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
        search_ui_url: AnysearchStore.get_search_ui_url()
        subscription_title: SubscriptionModalStore.get_subscription_title()
        subscription_category: SubscriptionModalStore.get_subscription_category()
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
    ui_url = btn.data('search_ui_url')
    title = btn.data('subscription_title')
    category = btn.data('subscription_category')
    SubscriptionModalActions.showModal(url, ui_url, title, category)
  )
)
