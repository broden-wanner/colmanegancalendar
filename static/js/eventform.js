var showHideDuration = 200;

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

//Append 'occurences' to ends_after input box
$('input[name="ends_after"]').parent().append(" occurences");

//Handles displaying of recurring event menu
var $repeatCheckBox = $('input[name="repeat"]');
var repeatingFields = ["repeat_every", "ends_on", "ends_after"];
var repeatingFieldObjects = [];

for(var i = 0; i < repeatingFields.length; i++) {
	stringOfField = 'input[name="' + repeatingFields[i] + '"]';
	repeatingFieldObjects.push($(stringOfField).parent());
}

repeatingFieldObjects.push($('label:contains("Duration:")'));
repeatingFieldObjects.push($("#id_duration"));
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
			repeatingFieldObjects[i].show(showHideDuration);
		}
	} else {
		for(var i = 0; i < repeatingFieldObjects.length; i++) {
			repeatingFieldObjects[i].hide(showHideDuration);
		}
	}
});

//Handles the checking of the duration field
var $dayAndMonthDuration = $('input:radio[value="1"], input:radio[value="3"]');
if($dayAndMonthDuration.is(":checked")) {
	$('label:contains("Repeat on:")').hide();
	$("#id_repeat_on").hide();
}
$dayAndMonthDuration.click(function() {
	if(this.checked) {
		$('label:contains("Repeat on:")').hide(showHideDuration);
		$("#id_repeat_on").hide(showHideDuration);
	}
});

var $weekDuration = $('input:radio[value="2"]');
if($weekDuration.is(":checked") && $repeatCheckBox.is(":checked")) {
	$('label:contains("Repeat on:")').show();
	$("#id_repeat_on").show();
}
$weekDuration.click(function() {
	if(this.checked) {
		$('label:contains("Repeat on:")').show(showHideDuration);
		$("#id_repeat_on").show(showHideDuration);
	}
});

//Handles the ends_on and ends_after fields
var $endsOn = $('input[name="ends_on"]');
var $endsAfter = $('input[name="ends_after"]').css("background-color", "LightGrey");
$endsOn.focusin(function() {
	$endsOn.css("background-color", "white");
	$endsAfter.val("").css("background-color", "LightGrey");
});
$endsAfter.focusin(function() {
	$endsAfter.css("background-color", "white");
	$endsOn.val("").css("background-color", "LightGrey");
});