$(document).ready(function(){
  const SELECTORS = {
    packageInput:  function() { return $("input[name=package]"); },
    getPackageInfo: function(packageId) { return $("#package_benefits_" + packageId); },
    getPackageBenefits: function(packageId) { return SELECTORS.getPackageInfo(packageId).children(); },
    benefitsInputs: function() { return $("input[id^=id_benefits_]"); },
    getBenefitInput: function(benefitId) { return SELECTORS.benefitsInputs().filter('[value=' + benefitId + ']'); },
    getSelectedBenefits: function() { return SELECTORS.benefitsInputs().filter(":checked"); },
  }

  SELECTORS.packageInput().change(function(){
    let package = this.value;
    if (package.length == 0) return;

    SELECTORS.getSelectedBenefits().each(function(){
      $(this).prop('checked', false);
    });

    $(".selected").removeClass("selected");
    SELECTORS.getPackageBenefits(package).each(function(){
      let benefit = $(this).html()
      let benefitInput = SELECTORS.getBenefitInput(benefit);
      benefitInput.prop("checked", true);
      $(`#benefit-${benefit}-package-${package}`).addClass("selected");
    });
  });
});
