$(document).ready(function() {
    if ($('#talk-summary').length && $('#talk-description').length) {
        $('#talk-summary').summernote({
            height: 150,
        });
        $('#talk-description').summernote({
            height: 150,
        });
    }

    $('#talk-summary').code($('#talk-summary').text())

    $('#talk-description').code($('#talk-description').text())

    $('#talk-form').on('submit', function() {
        var talk_summary = $('textarea[name="talk-summary"]').html($('#talk-summary').code());
        var talk_description = $('textarea[name="talk-description"]').html($('#talk-description').code());
    });
});