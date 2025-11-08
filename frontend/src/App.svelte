<script lang="ts">
  let input = $state("What the Segma?");
  let output = $state("")

  function segment(text) {
    return text;
  }

  function segmentInput() {
    console.log("run")
    output = segment(input)
  }
</script>

<input value={input} style="background: red"/>
<br>
<button onclick={()=>{alert("hi"); segmentInput()}}>
  #mybutton
</button>
<br>
Segmented: {output}

<style>

</style>
