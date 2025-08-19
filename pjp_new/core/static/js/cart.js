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

  // Update qty in cart page
  document.querySelectorAll(".qty-input").forEach(function(input){
    input.addEventListener("change", function(){
      const id = this.dataset.id;
      const qty = this.value;
      fetch("/cart/update/", {
        method: "POST",
        headers: {"X-CSRFToken": csrftoken, "Content-Type":"application/x-www-form-urlencoded"},
        body: new URLSearchParams({item_id: id, quantity: qty})
      }).then(r=>r.json()).then(d=>{
        if (d.success){
          location.reload();
        }
      });
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
