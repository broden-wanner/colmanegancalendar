var showHideDuration = 200;

//Adds date and time pickers to forms
$(function() {
	$('input[name="start_date"], input[name="end_date"], input[name="ends_on"]').datepicker();
	$('input[name="start_time"], input[name="end_time"]').timepicker({
		timeFormat: 'hh:mm p',
		interval: 15
	});
});


//Handles the showing and hiding of the time boxes depending on all_day
var $allDayBox = $('input[name="all_day"]');
var $startTimeInput = $('input[name="start_time"]').parent();
var $endTimeInput = $('input[name="end_time"]').parent();

if($allDayBox.is(":checked")) {
    $startTimeInput.hide();
    $endTimeInput.hide();
}

$allDayBox.click(function() { 
	if(this.checked) {
		$startTimeInput.hide(showHideDuration);
		$endTimeInput.hide(showHideDuration);
	} else {
		$startTimeInput.show(showHideDuration);
		$endTimeInput.show(showHideDuration);
	}
});



//Handles displaying of recurring event menu
var $repeatCheckBox = $('input[name="repeat"]');
var repeatingFields = ["repeat_every", "ends_on", "ends_after"];
var repeatingFieldObjects = [];

for(var i = 0; i < repeatingFields.length; i++) {
	stringOfField = 'input[name="' + repeatingFields[i] + '"]';
	repeatingFieldObjects.push($(stringOfField).parent());
}

repeatingFieldObjects.push($('select[name="duration"]').parent());
repeatingFieldObjects.push($('label:contains("Repeat on:")'));
repeatingFieldObjects.push($("#id_repeat_on"));

if(!$repeatCheckBox.is(":checked")){
	for(var i = 0; i < repeatingFieldObjects.length; i++) {
		repeatingFieldObjects[i].hide();
	}
}

$repeatCheckBox.click(function() {
	if(this.checked) {
		for(var i = 0; i < repeatingFieldObjects.length; i++) {
			if(i != 4 && i != 5) {
				repeatingFieldObjects[i].show(showHideDuration);
			} else if((i == 4 || i == 5) && $('select[name="duration"]').val() != 1) {
				repeatingFieldObjects[i].show(showHideDuration);
			}
		}
	} else {
		for(var i = 0; i < repeatingFieldObjects.length; i++) {
			repeatingFieldObjects[i].hide(showHideDuration);
		}
	}
});




//Handles the checking of the duration field
var $durationSelector = $('select[name="duration"]');

function toggleRepeatOn(showhide) {
	if(showhide == "hide") {
		$('label:contains("Repeat on:")').hide(showHideDuration);
		$("#id_repeat_on").hide(showHideDuration);
	} else if (showhide == "show") {
		$('label:contains("Repeat on:")').show(showHideDuration);
		$("#id_repeat_on").show(showHideDuration);
	} else if (showhide == "immediately hide") {
		$('label:contains("Repeat on:")').hide();
		$("#id_repeat_on").hide();
	}
}

if($durationSelector.val() == 1 || $durationSelector.val() == 3) {
	toggleRepeatOn("immediately hide");
}

$durationSelector.click(function() {
	if($(this).val() == 1 || $(this).val() == 3) {
		toggleRepeatOn("hide");
	} else if ($(this).val() == 2) {
		toggleRepeatOn("show");
	}
});




//Handles the ends_on and ends_after fields
var $endsOn = $('input[name="ends_on"]');
var $endsAfter = $('input[name="ends_after"]');
if ($endsOn.val() == "" && $endsAfter.val() == "") {
	$endsAfter.css("background-color", "LightGrey");
} else if($endsOn.val() == "" && $endsAfter.val() != "") {
	$endsOn.css("background-color", "LightGrey");
} else {
	$endsAfter.css("background-color", "LightGrey");
}

$endsOn.focusin(function() {
	$endsOn.css("background-color", "white");
	$endsAfter.val("").css("background-color", "LightGrey");
});
$endsAfter.focusin(function() {
	$endsAfter.css("background-color", "white");
	$endsOn.val("").css("background-color", "LightGrey");
});