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
		console.log("repeat box is checked");
	} else {
		for(var i = 0; i < repeatingFieldObjects.length; i++) {
			repeatingFieldObjects[i].hide(showHideDuration);
		}
	}
});

//Append 'occurences' to ends_after input box
$('input[name="ends_after"]').parent().append(" occurences");