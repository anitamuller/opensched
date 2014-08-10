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

    $scope.changeImage = function() {
        $scope.image = '/static/img/checked.png';
    }
}