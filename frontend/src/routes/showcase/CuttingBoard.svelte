<script>
  const Stage = {
    BEFORE: 0,
    WORDS: 1,
  };

  let input = $state("What the Segma?");
  let stage = $state(Stage.BEFORE);
  let words = $state(splitWords(input));
  
  function splitWords(text) {
    return text.replace(/\s/g, " ").split(" ");
  }

  function segment(text) {
    return text.split(" ").map((word)=>word.split(""));
  }

  export function startAnimation(){
    words = splitWords(input);
    console.log(input);
    console.log(words);
    stage = Stage.WORDS;
  }
</script>

<div id=cutting-board>
  {#if stage == Stage.BEFORE}
    <div id=cutting-board-input bind:innerText={input} contenteditable=true />
  {:else if stage == Stage.WORDS}
    <div id="word-container">
      {#each words as word}
        <span class="word">
          <span>
            {word}
          </span>
        </span>&nbsp<span class="word-spacer" />
      {/each}
    </div>
  {/if}
</div>

<style>
  @import "./style.css";
  
  #cutting-board {
    align-items: center;
    justify-content: center;
    display: flex;
  }

  #word-container {
    width: 100%;
    margin: 2em;  
  }

  .word {
    display: inline-block;
    margin: 0.25em 0 0.25em 0;
  }

  .word > span {
    background-color: blue;
    padding: 0.1em;
  }

  .word-spacer {
    animation: 1s ease-out 0.2s 1 both expand;
    animation-iteration-count: 1;
    background-color: red;
    display: inline-block;
  }

  @keyframes expand {
    from {
      width: 0em;
    }
    to {
      width: 1em;
    }
  }
</style>
