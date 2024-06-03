odoo.define("booking_room.room_view_tree", function (require) {
  "use strict";
  var ListRenderer = require("web.ListRenderer");
  var viewRegistry = require("web.view_registry");
  var ListView = require("web.ListView");
  var field_utils = require('web.field_utils');
  var FIELD_CLASSES = {
    char: 'o_list_char',
    float: 'o_list_number',
    integer: 'o_list_number',
    monetary: 'o_list_number',
    text: 'o_list_text',
    many2one: 'o_list_many2one',
};
  var CustomListRenderer = ListRenderer.extend({
    _renderBodyCell: function (record, node, colIndex, options) {
      var tdClassName = 'o_data_cell';
      if (node.tag === 'button_group') {
          tdClassName += ' o_list_button';
      } else if (node.tag === 'field') {
          tdClassName += ' o_field_cell';
          var typeClass = FIELD_CLASSES[this.state.fields[node.attrs.name].type];
          if (typeClass) {
              tdClassName += (' ' + typeClass);
          }
          if (node.attrs.widget) {
              tdClassName += (' o_' + node.attrs.widget + '_cell');
          }
      }
      if (node.attrs.editOnly) {
          tdClassName += ' oe_edit_only';
      }
      if (node.attrs.readOnly) {
          tdClassName += ' oe_read_only';
      }
      var $td = $('<td>', { class: tdClassName, tabindex: -1 });

      // We register modifiers on the <td> element so that it gets the correct
      // modifiers classes (for styling)
      var modifiers = this._registerModifiers(node, record, $td, _.pick(options, 'mode'));
      // If the invisible modifiers is true, the <td> element is left empty.
      // Indeed, if the modifiers was to change the whole cell would be
      // rerendered anyway.
      if (modifiers.invisible && !(options && options.renderInvisible)) {
          return $td;
      }

      if (node.tag === 'button_group') {
          for (const buttonNode of node.children) {
              if (!this.columnInvisibleFields[buttonNode.attrs.name]) {
                  $td.append(this._renderButton(record, buttonNode));
              }
          }
          return $td;
      } else if (node.tag === 'widget') {
          return $td.append(this._renderWidget(record, node));
      }
      if (node.attrs.widget || (options && options.renderWidgets)) {
          var $el = this._renderFieldWidget(node, record, _.pick(options, 'mode'));
          return $td.append($el);
      }
      this._handleAttributes($td, node);
      this._setDecorationClasses($td, this.fieldDecorations[node.attrs.name], record);

      var name = node.attrs.name;
      var field = this.state.fields[name];
      var value = record.data[name];
      var formatter = field_utils.format[field.type];
      var formatOptions = {
          escape: true,
          data: record.data,
          isPassword: 'password' in node.attrs,
          digits: node.attrs.digits && JSON.parse(node.attrs.digits),
      };
      var formattedValue = formatter(value, field, formatOptions);
      var title = '';
      if (field.type !== 'boolean') {
          title = formatter(value, field, _.extend(formatOptions, {escape: false}));
      }
      return $td.html(formattedValue).attr('title', title).attr('name', name).attr('id', "booking-room-custom_des");
  },
    _renderBody: function () {
      var self = this;
      var $rows = this._renderRows();
      while ($rows.length < 4) {
        $rows.push(self._renderEmptyRow());
      }

      // Add row numbers only to non-empty rows
      var rowNumber = 1;
      $rows.forEach(function ($row) {
        // Check if the row has any non-empty cells
        var hasData = $row
          .children()
          .toArray()
          .some(function (cell) {
            return $(cell).text().trim() !== "";
          });
        if (hasData) {
          var $cells = $row.children();
          $('<td class="o_data_cell">')
            .text(rowNumber)
            .insertAfter($cells.first());
          rowNumber++;
        }
      });

      return $("<tbody>").append($rows);
    },

    _renderHeader: function (isGrouped) {
      var $tr = $("<tr>").append(
        _.map(this.columns, this._renderHeaderCell.bind(this))
      );
      if (this.hasSelectors) {
        $tr.prepend(this._renderSelector("th"));
      }
      $('<th class="o_column_sortable">No.</th>').insertAfter(
        $tr.find("th").first()
      ); // Add header for row numbers in the second column
      return $("<thead>").append($tr);
    },

    _renderFooter: function () {
      var aggregates = {};
      _.each(this.columns, function (column) {
        if ("aggregate" in column) {
          aggregates[column.attrs.name] = column.aggregate;
        }
      });
      var $cells = this._renderAggregateCells(aggregates);
      if (this.hasSelectors) {
        $cells.unshift($("<td>"));
      }
      $cells.push($("<td>"));
      return $("<tfoot>").append($("<tr>").append($cells));
    },
  });

  var CustomBasicView = ListView.extend({
    config: Object.assign({}, ListView.prototype.config, {
      Renderer: CustomListRenderer,
    }),
  });

  viewRegistry.add("list_view", CustomBasicView);
});
