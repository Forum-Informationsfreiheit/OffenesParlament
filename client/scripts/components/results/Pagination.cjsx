React = require 'react'
AnysearchActions = require '../../actions/AnysearchActions.coffee'
classnames = require 'classnames'


Pagination = React.createClass

  getInitialState: () ->
    return {}

  componentDidMount: () ->
    return

  componentWillUnmount: () ->
    return

  _is_back_arrow_active: () ->
    return @props.offset > 0

  _is_forward_arrow_active: () ->
    return @props.offset + @props.items_per_page < @props.max_items

  _get_page_count: () ->
    return Math.ceil(@props.max_items / @props.items_per_page)

  _get_current_page: () ->
    return Math.round(@props.offset / @props.items_per_page) + 1

  _change_offset: (pages) ->
    new_offset = (Math.min(@_get_current_page() + pages, @_get_page_count()) - 1) * @props.items_per_page
    new_offset = Math.max(new_offset, 0)
    AnysearchActions.updatePaginationOffset(new_offset)

  render: ->
    current_page = @_get_current_page()
    pages = []
    start = Math.max(1, current_page - 5)
    end = Math.min(@_get_page_count(), current_page + 5)
    for i in [start..end]
      click_handler = ((count) =>
        return (e) =>
          e.preventDefault()
          AnysearchActions.updatePaginationOffset(count * @props.items_per_page)
      )(i-1)
      pages.push <li key={i} className={classnames('current': (i==current_page))}><a href="#" onClick={click_handler}>{i}</a></li>
    <ul className="pagination">
      <li><a href="#" onClick={(e) => e.preventDefault(); @_change_offset(-1)} className={classnames('back', 'disabled': !@_is_back_arrow_active())}></a></li>
      {pages}
      <li><a href="#" onClick={(e) => e.preventDefault(); @_change_offset(1)} className={classnames('forward', 'disabled': !@_is_forward_arrow_active())}></a></li>
    </ul>

module.exports = Pagination

