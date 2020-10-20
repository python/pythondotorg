$(document).ready(function(){
    let checkboxesContainer = $('#benefits_container');
    $("#clear_form_btn").click(function(){
        $("#application_form").trigger("reset");
    })

    $("input[name=package]").change(function(){
      let package = this.value;
      if (package.length == 0) return;

      checkboxesContainer.find(':checkbox').each(function(){
          $(this).prop('checked', false);
      });

      $("#package_benefits_" + package).children().each(function(){
          let benefit = $(this).html()
          checkboxesContainer.find(`[value=${benefit}]`).prop("checked", true);
      });

      let url = $("#cost_container").attr("calculate_cost_url");
      let data = $("form").serialize();

      $.get(url, data).done(function(data){
          let cost = data.cost;
          $("#cost_label").html(`Sponsorship cost is $${cost}.00`)
          $("#cost_container").show();
      })
    });

    $("input[id^=id_benefits_]").change(function(){
      let benefit = this.value;
      if (benefit.length == 0) return;

      let active = checkboxesContainer.find(`[value=${benefit}]`).prop("checked");
      if (!active) return;

      $(`#conflicts_with_${benefit}`).children().each(function(){
          let conflictId = $(this).html();
          let conflictCheckbox = checkboxesContainer.find(`[value=${conflictId}]`);
          let checked = conflictCheckbox.prop("checked");
          if (checked) conflictCheckbox.trigger("click");
      });
      $("#cost_container").hide();
    });
});
