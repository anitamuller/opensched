$(function() {
    if ($('#event-summary').length && $('#event-description').length) {
        $('#event-summary').summernote({
            height: 150,
            toolbar: [
                //[groupname, [button list]]

                ['style', ['bold', 'italic', 'underline', 'clear']],
                ['font', ['strikethrough']],
                ['fontsize', ['fontsize']],
                ['color', ['color']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['height', ['height']],
                ['fullscreen', ['fullscreen']],
                ['codeview', ['codeview']],
                ['help', ['help']],
            ]
        });
        $('#event-description').summernote({
            height: 150,
        });
    }

    $('#event-summary').code($('#event-summary').text())

    $('#event-description').code($('#event-description').text())

    $('#event-form').on('submit', function() {
        var event_summary = $('textarea[name="event-summary"]').html($('#event-summary').code());
        var event_description = $('textarea[name="event-description"]').html($('#event-description').code());
    });
});