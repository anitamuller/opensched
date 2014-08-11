var singleEvent = angular.module('singleEvent', []);

function singleEventController($scope) {
    $scope.showSchedule = true;
    $scope.showSpeakers = false;
    $scope.showAttendees = false;

    $scope.clickSchedule = function() {
        if ($scope.showSchedule == false) {
            $scope.showSpeakers = false;
            $scope.showAttendees = false;
            $scope.showSchedule = !$scope.showSchedule;
        }
    }

    $scope.clickSpeakers = function() {
        if ($scope.showSpeakers == false) {
            $scope.showSchedule = false;
            $scope.showAttendees = false;
            $scope.showSpeakers = !$scope.showSpeakers;
        }
    };
    $scope.clickAttendees = function() {
        if ($scope.showAttendees == false) {
            $scope.showSchedule = false;
            $scope.showSpeakers = false;
            $scope.showAttendees = !$scope.showAttendees;
        }
    };

    $scope.addSched = function(talk_permalink) {
        var event_permalink = $('#event-permalink').text()
        var user_email = $('#user-email').text()

        if (user_email != "") {
            $.ajax({
                url: 'http://localhost:8080/schedule_talk_event',
                type: 'POST',
                data: JSON.stringify({'event_permalink': event_permalink,
                                      'talk_permalink': talk_permalink,
                                      'user_email': user_email}),
                contentType: "application/json; charset=utf-8",
            }).done(function() {
                window.location.reload()
            });
        } else {
            alert('Login or sign up to bookmark your favorite talks.');
        }
    }

    $(".select-talk")
        .mouseover(function() {
            if ($(this).attr("src") != '/static/img/checked.png') {
                var src = '/static/img/hover-checked.png';
                var style = 'opacity: 0.4; filter: alpha(opacity=40);'
                $(this).attr("src", src);
                $(this).attr("style", style);
            }
        })
        .mouseout(function() {
            if ($(this).attr("src") != '/static/img/checked.png') {
                var src = '/static/img/unchecked.png';
                var style = 'opacity: 1.0; filter: alpha(opacity=100);'
                $(this).attr("src", src);
                $(this).attr("style", style);
            }
        });
}