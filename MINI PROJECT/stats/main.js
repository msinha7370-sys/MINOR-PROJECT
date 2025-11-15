// Poll top-level attractions periodically and update displayed crowd percentages on index
function updateCrowds(){
  // find elements with id crowd-<id>
  $("[id^=crowd-]").each(function(){
    const id = this.id.split('-')[1];
    $.getJSON("/api/status/" + id, function(data){
      if (data && data.crowd !== undefined) {
        $("#crowd-" + id).text(data.crowd);
      }
    });
  });
}
setInterval(updateCrowds, 4000);
$(document).ready(updateCrowds);
