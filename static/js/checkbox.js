$(function() {
    $('#select-all').on('click', function() {
        if (this.checked) {
            // Select all events
            $('.delete-event').each(function() {
                this.checked = true;
            });
            // Select all talks
            $('.delete-talk').each(function() {
                this.checked = true;
            });
        } else {
            // Unselect all events
            $('.delete-event').each(function() {
                this.checked = false;
            });
            // Unselect all talks
            $('.delete-talk').each(function() {
                this.checked = false;
            });
        }
    });

    $('.checkbox-bulk').on('click', function() {
        all_selected = true;

        $('.checkbox-bulk').each(function() {
            if (this.checked == false) {
                all_selected = false;
            }
        });

        if (all_selected) {
            $('#select-all').prop("checked", true);
        } else {
            $('#select-all').prop("checked", false);
        }
    });

});