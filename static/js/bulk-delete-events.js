var formApp = angular.module('formApp', []);

$("#delete-events").prop("disabled", true);

function eventsController($scope) {

    $scope.clickDelete = function() {
        none_selected = true;

        $('.delete-event').each(function() { // loop through each checkbox
            if (this.checked)
                none_selected = false;
        });

        if (none_selected)
            $("#delete-events").prop("disabled", true);
        else
            $("#delete-events").prop("disabled", false);
    };

    $scope.eventsToDelete = function() {
        event_list = []
        $('.delete-event').each(function() { // loop through each checkbox
            if (this.checked)
                event_list.push(this.value)
        });

        $.ajax({
            url: 'http://localhost:8080/bulk_delete_events',
            type: 'POST',
            data: JSON.stringify({
                events_to_remove: event_list
            }),
            contentType: "application/json; charset=utf-8",
        }).done(function() {
            window.location.reload()
        });
    };
}