var buttonCommon = {
    exportOptions: {
        format: {
            header: function (data) {
              return $(data)
                .find("span")
                .remove()
                .end()
                .text()
                  }
                },
            },
        };
var tableDefault = {
                dom: '<"top">Bfrti<"bottom"lp>',
                buttons: [
                    $.extend( true, {}, buttonCommon, {
                        extend: 'copyHtml5',
                        title: ""
                        } ),
                    $.extend( true, {}, buttonCommon, {
                        text: 'TSV',
                        extend: 'csvHtml5',
                        fieldSeparator: '\t',
                        fieldBoundary: '',
                        extension: '.tsv'
                    }),
                ],
                "pageLength": 5,
                "lengthMenu": [[5, 20, 50, -1], [5, 20, 50, "All"]],
                responsive: true
        }
