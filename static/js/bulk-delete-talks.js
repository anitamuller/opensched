var formApp = angular.module('formApp', []);

$("#delete-talks").prop("disabled", true);

function talksController($scope) {

    $scope.clickDelete = function() {
        none_selected = true;

        $('.delete-talk').each(function() { // loop through each checkbox
            if (this.checked)
                none_selected = false;
        });

        if (none_selected)
            $("#delete-talks").prop("disabled", true);
        else
            $("#delete-talks").prop("disabled", false);
    };

    $scope.talksToDelete = function() {
        talk_list = []
        $('.delete-talk').each(function() { // loop through each checkbox
            if (this.checked)
                talk_list.push(this.value)
        });

        $.ajax({
            url: 'http://localhost:8080/bulk_delete_talks',
            type: 'POST',
            data: JSON.stringify({
                talks_to_remove: talk_list
            }),
            contentType: "application/json; charset=utf-8",
        }).done(function() {
            window.location.reload()
        });
    };
}