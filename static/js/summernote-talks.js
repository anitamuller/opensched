$(document).ready(function() {
    if ($('#talk-summary').length && $('#talk-description').length) {
        $('#talk-summary').summernote({
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
        $('#talk-description').summernote({
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
    var talk_form = function() {
        var talk_summary = $('textarea[name="talk-summary"]').html($('#talk-summary').code());
        var talk_description = $('textarea[name="talk-description"]').html($('#talk-description').code());
    }
});