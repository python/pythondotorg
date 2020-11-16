$(document).ready(function(){
    let checkboxesContainer = $('#benefits_container');
    let costLabel = $("#cost_label");
    let cost = 0;

    $("#clear_form_btn").click(function(){
        $("#application_form").trigger("reset");
        $("#application_form [class=active]").removeClass("active");
        $("#cost_label").html("Select a package or customize the benefits");
    });

    $("input[name=package]").change(function(){
      let package = this.value;
      if (package.length == 0) return;

      costLabel.html("Updating cost...")

      checkboxesContainer.find(':checkbox').each(function(){
          $(this).prop('checked', false);
          let packageOnlyBenefit = $(this).attr("package_only");
          if (packageOnlyBenefit) $(this).attr("disabled", true);
      });

      let packageInfo = $("#package_benefits_" + package);
      packageInfo.children().each(function(){
          let benefit = $(this).html()
          let benefitInput = checkboxesContainer.find('[value=' + benefit + ']');
          let packageOnlyBenefit = benefitInput.attr("package_only");
          benefitInput.removeAttr("disabled");
          benefitInput.trigger("click");
      });

      let url = $("#cost_container").attr("calculate_cost_url");
      let data = $("form").serialize();

      let cost = packageInfo.attr("data-cost");
      costLabel.html('Sponsorship cost is $' + cost.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") + ' USD')
    });

    $("input[id^=id_benefits_]").change(function(){
      let benefit = this.value;
      if (benefit.length == 0) return;
      if (costLabel.html() != "Updating cost...") costLabel.html("Submit your application and we'll get in touch...");

      let active = checkboxesContainer.find('[value=' + benefit + ']').prop("checked");
      if (!active) {
          let packageOnlyBenefit = $(this).attr("package_only");
          if (packageOnlyBenefit) $(this).attr("disabled", true);
          return;
      } else {
          $('label[benefit_id=' + benefit + ']').addClass("active");
      }


      $('#conflicts_with_' + benefit).children().each(function(){
          let conflictId = $(this).html();
          let conflictCheckbox = checkboxesContainer.find('[value=' + conflictId + ']');
          let checked = conflictCheckbox.prop("checked");
          if (checked){
            conflictCheckbox.trigger("click");
            conflictCheckbox.parent().removeClass("active");
          }
      });
    });
});
