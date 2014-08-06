window.MDM_SILENT = true;
$(function() {
    $('a[data-target="_blank"]').attr('target', '_blank');

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

    $('#event-preview').on('click', function() {
        var eventForm = $('#event-form');
        eventForm.find('#preview').val('1');
    });
    $('#event-submit').on('click', function() {
        var eventForm = $('#event-form');
        eventForm.find('#preview').val('');
    });

    $('#talk-preview').on('click', function() {
        var talkForm = $('#talk-form');
        talkForm.find('#preview').val('1');
    });

    $('#talk-submit').on('click', function() {
        var talkForm = $('#talk-form');
        talkForm.find('#preview').val('');
    });


    $('a.icon').on('click', function() {
        return confirm('Are you sure?');
    });
});