<style media="screen">
  .newsletter-block{
    background: #c8bda3;
    padding: 28px;
    padding-bottom: 13px;
    margin-bottom: 14px;
    margin-top: 1rem;
    text-align: center;
  }
  .newsletter-block h4{
    color: #fff;
    font-size: 1.3rem;
    font-weight: 100;
  }
  .newsletter-block h3{
    color: #000;
    font-size: 1.6rem;
    font-weight: 100;
  }
  .newsletter-block .terms{
    font-size: .8rem;
    color: #fff;
    font-weight: 400;
    margin-top: 10px;
    padding: 0 60px;
  }
  .newsletter-block .terms a{
    font-size: .8rem;
    color: #fff;
    font-weight: 400;
    text-decoration: underline;
  }

  .newsletter-block form .input-wrapper{
    text-transform: uppercase;
    font-weight: 400;
    box-shadow: none;
    border-radius: 0;
    color: #fff;
    border-color: transparent;
  }
  .newsletter-block form .input-wrapper{
    overflow: hidden;
  }
  .newsletter-block form input[type=email], .newsletter-block form input[type=email]:focus {
    border: 1px solid #ffffff;
    outline: 0;
    width: 100%;
    box-shadow: none;
    padding: 7px 20px;
    height: 45px;
    line-height: 1;
    font-weight: 400;
  }
  .newsletter-form-wrapper{
    position: relative;
    padding-top: 10px;
  }
  .newsletter-form .btn-primary{
    font-size: .8rem;
  }

</style>

<section>
  <div class="container">
    <div class="row">
      <div class="col-md-12">
        <div class="newsletter-block">
          <div class="row">
            <div class="col-lg-3 col-md-12"></div>
            <div class="col-lg-6 col-md-12">
              <h4>the best you can get</h2>
              <h3>SUBSCRIBE FOR A <strong>10% DISCOUNT</strong></h1>

              <div class="newsletter-form-wrapper">
                <form class="newsletter-form" action="index.html" method="post">
                  <div class="row">
                     <div class="col-xs-12">
                        <input class="btn btn-primary float-xs-right" name="submitNewsletter" type="submit" value="Subscrever">
                        <div class="input-wrapper">
                           <input name="email" type="email" value="" placeholder="O seu endereço de e-mail" aria-labelledby="block-newsletter-label">
                        </div>
                        <input type="hidden" name="action" value="0">
                        <div class="clearfix"></div>
                     </div>
                  </div>
                </form>

                <p class="terms">By subscribing you agree with our <a href="#">Terms & Conditions</a> and <a href="#">Privacy Policy</a>. To opt out, click unsubscribe at the bottom of our emails</p>
              </div>

            </div>
            <div class="col-lg-3 col-md-12"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>