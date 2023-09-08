$(document).ready(function() {
    // Store the initial list of components
    var initialComponents = $('#id_components').html();
  
    // Handle changes to component dropdown and quantity fields
    $(document).on('change', '.component-select, .quantity-input', function() {
      // Get the selected component and its quantity
      var selectedComponent = $(this).closest('.inline-related').find('.component-select').val();
      var quantity = $(this).closest('.inline-related').find('.quantity-input').val();
  
      // Remove the selected component from the dropdown options
      $('#id_components option').each(function() {
        if ($(this).val() == selectedComponent) {
          $(this).remove();
        }
      });
  
      // Add the selected component back to the dropdown if quantity is cleared/empty
      if (!quantity || quantity.trim() === '') {
        $('#id_components').append('<option value="' + selectedComponent + '">' + selectedComponent + '</option>');
      }
    });
  
    // Handle clicking the "Add another" button
    $(document).on('click', '.add-row a', function() {
      // Reset the components dropdown to the initial state
      $('#id_components').html(initialComponents);
    });
  });