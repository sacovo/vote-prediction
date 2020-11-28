$(document).ready(function(){
  $.fn.dataTable.render.boolean = function () {
    return function ( data, type, row ) {
      if ( type === 'display' ) {
        return data ? '&#10003;' : '&#10799;';
      }
      return data;
    };
  };

  var params = new URLSearchParams(window.location.search);
  var vote_index = params.get('vote-index') || 0;
  let float_renderer = $.fn.dataTable.render.number('\'', '.', 2);
  let int_renderer = $.fn.dataTable.render.number('\'', '.', 0);

  let gemeinden = $('#gemeinden').DataTable({
    'ajax': {
      "url": `gemeinden/${vote_index}/latest.json`,
      "dataSrc": "",
    },
    "dom": "lfBrtip",
    "fixedHeader": true,
    "buttons": [ 'copy', 'csv', 'excel' ],
    "columns": [
      {'data': 'Gemeinde'},
      {'data': 'Kanton'},
      {'data': "JaInProzent", 'render': float_renderer, 'className': 'text-right'},
      {'data': 'StimmbetProzent', 'render': float_renderer, 'className': 'text-right'},
      {'data': 'Stimmberechtigte', 'render': int_renderer, 'className': 'text-right'},
      {'data': 'Ausgezaehlt', 'render': $.fn.dataTable.render.boolean()},
      {'data': 'JaTotal', 'render': int_renderer, 'className': 'text-right'},
      {'data': 'NeinTotal', 'render': int_renderer, 'className': 'text-right'},
    ],
    "stateSave": true,
  });

  let kantone = $('#kantone').DataTable({
    'ajax': {
      "url": `kantone/${vote_index}/latest.json`,
      "dataSrc": "",
    },
    "fixedHeader": true,
    "dom": "lfBrtip",
    'paging': false,
    "buttons": [ 'copy', 'csv', 'excel' ],
    "columns": [
      {'data': 'Kanton'},
      {'data': 'JaTotal', 'render': int_renderer, 'className': 'text-right'},
      {'data': 'NeinTotal', 'render': int_renderer, 'className': 'text-right'},
      {'data': "JaInProzent", 'render': float_renderer, 'className': 'text-right'},
    ],
    "stateSave": true,
  });

  let schweiz = $('#schweiz').DataTable({
    'ajax': {
      'url': `schweiz/${vote_index}/latest.json`,
      'dataSrc': "",
    },
    'dom': 't',
    'columns': [
      {'data': 'kantone', 'render': int_renderer, 'className': 'text-right'},
      {'data': 'ja_prozent', 'render': float_renderer, 'className': 'text-right'},
      {'data': 'ja_total', 'render': int_renderer, 'className': 'text-right'},
    ]
  });

  setInterval( function () {
    let p = gemeinden.page();
    gemeinden.ajax.reload(function(){
      gemeinden.page(p).draw('page');
    }, false);
  }, 5000 );

  setInterval( function () {
    let p = kantone.page();
    kantone.ajax.reload(function(){
      kantone.page(p).draw('page');
    }, false);
  }, 5000 );

  setInterval( function () {
    schweiz.ajax.reload();
  }, 5000 );
});
