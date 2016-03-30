React = require 'react'
_ = require 'underscore'
AnysearchStore = require '../../stores/AnysearchStore.coffee'


_get_state_from_store = () ->
  return {
    result_count: AnysearchStore.get_result_count()
  }



ResultsPreview = React.createClass

  getInitialState: () ->
    return _get_state_from_store()

  componentDidMount: () ->
    AnysearchStore.addChangeListener(@_onChange)

  componentWillUnmount: () ->
    AnysearchStore.removeChangeListener(@_onChange)

  _onChange: () ->
    @setState(_get_state_from_store())

  render: ->
    if _.isNull(@state.result_count)
      sentence = ''
    else
      sentence = 'Diese Suche liefert ' + @state.result_count + ' Ergebnisse.'
      if @state.result_count == 0
        sentence = 'Diese Suche liefert keine Ergebnisse.'
      else if @state.result_count == 1
        sentence = 'Diese Suche liefert ' + @state.result_count + ' Ergebnis.'
    <span>{sentence}</span>

module.exports = ResultsPreview
