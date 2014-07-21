window.MDM_SILENT = true;
$(function(){
    $('a[data-target="_blank"]').attr('target', '_blank');

    if($('#post-short').length && $('#post-full').length) {
        $('#post-short').mdmagick();
        $('#post-full').mdmagick();
    }

    if($('#event-summary').length && $('#event-description').length) {
        $('#event-summary').mdmagick();
        $('#event-description').mdmagick();
    }

    $('.post .article img').each(function(index, el){
        var anchor = '<a href="'+$(el).attr('src')+'" title="'+$(el).attr('alt')+'" data-lightbox="'+$(el).attr('src')+'"><img src="'+$(el).attr('src')+'" alt="'+$(el).attr('alt')+'"></a>';
        $(el).replaceWith(anchor);
    });

    $('#post-preview').on('click', function(){
        var postForm = $('#post-form');
        postForm.find('#preview').val('1');
    });
    $('#post-submit').on('click', function(){
        var postForm = $('#post-form');
        postForm.find('#preview').val('');
    });

    $('#event-preview').on('click', function(){
        var eventForm = $('#event-form');
        eventForm.find('#preview').val('1');
    });
    $('#event-submit').on('click', function(){
        var eventForm = $('#event-form');
        eventForm.find('#preview').val('');
    });

    $('a.icon').on('click', function(){
        return confirm('Are you sure?');
    });
});
