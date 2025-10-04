document.addEventListener("DOMContentLoaded", function(){
  // Add to cart btns
  document.querySelectorAll(".add-to-cart").forEach(function(btn){
    btn.addEventListener("click", function(){
      const id = this.dataset.id;
      fetch("/cart/add/", {
        method: "POST",
        headers: {"X-CSRFToken": csrftoken, "Content-Type":"application/x-www-form-urlencoded"},
        body: new URLSearchParams({product_id: id, quantity:1})
      }).then(r=>r.json()).then(d=>{
        if (d.success){
          const el = document.getElementById("cart-count");
          if (el) el.innerText = d.cart_count;
        } else {
          alert("Could not add to cart.");
        }
      });
    });
  });

  // Function to update cart total
  function updateCartTotal() {
    let total = 0;
    document.querySelectorAll('.item-sub').forEach(function(cell) {
      const subtotal = parseFloat(cell.textContent) || 0;
      total += subtotal;
    });
    
    const totalElement = document.getElementById('cart-total');
    if (totalElement) {
      totalElement.textContent = total.toFixed(2);
    }
  }

  // Update qty in cart page
  document.querySelectorAll(".qty-input").forEach(function(input){
    input.addEventListener("change", function(){
      const id = this.dataset.id;
      const qty = this.value;
      console.log("Updating quantity:", id, qty); // Debug log
      
      fetch("/cart/update/", {
        method: "POST",
        headers: {"X-CSRFToken": csrftoken, "Content-Type":"application/x-www-form-urlencoded"},
        body: new URLSearchParams({item_id: id, quantity: qty})
      }).then(r=>r.json()).then(d=>{
        console.log("Update response:", d); // Debug log
        if (d.success){
          location.reload();
        } else {
          alert("Could not update quantity.");
        }
      }).catch(e=>{
        console.error("Update error:", e); // Debug log
        alert("Error updating quantity.");
      });
    });
    
    // Also listen for input event for immediate feedback
    input.addEventListener("input", function(){
      // Call the updateCartTotals function from cart template if it exists
      if (typeof updateCartTotals === 'function') {
        updateCartTotals();
      } else {
        // Fallback calculation
        updateCartTotal();
      }
    });
  });

  // Remove item
  document.querySelectorAll(".remove-item").forEach(function(btn){
    btn.addEventListener("click", function(){
      const id = this.dataset.id;
      fetch("/cart/remove/", {
        method: "POST",
        headers: {"X-CSRFToken": csrftoken, "Content-Type":"application/x-www-form-urlencoded"},
        body: new URLSearchParams({item_id: id})
      }).then(r=>r.json()).then(d=>{
        if (d.success) location.reload();
      });
    });
  });
});
