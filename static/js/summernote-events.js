$(document).ready(function() {
    if ($('#event-summary').length && $('#event-description').length) {
        $('#event-summary').summernote({
            height: 150,
            toolbar: [
                ['style', ['bold', 'italic', 'underline', 'clear']],
                ['font', ['strikethrough']],
                ['fontsize', ['fontsize']],
                ['color', ['color']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['height', ['height']],
            ]
        });
        $('#event-description').summernote({
            height: 150,
            toolbar: [
                ['style', ['bold', 'italic', 'underline', 'clear']],
                ['font', ['strikethrough']],
                ['fontsize', ['fontsize']],
                ['color', ['color']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['height', ['height']],
            ]
        });
    }

    var event_form = function() {
        var event_summary = $('textarea[name="event-summary"]').html($('#event-summary').code());
        var event_description = $('textarea[name="event-description"]').html($('#event-description').code());
    }
});