<script>
  let input = $state("What the Segma?");
  
  function segment(text) {
    return text.split(" ").map((word)=>word.split(""));
  }

  export function startAnimation(){
    alert("animation yay")
  }
</script> 

<div id=cutting-board>
<input value={input} />
</div>
